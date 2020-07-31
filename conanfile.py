import glob
import os
from conans import ConanFile, CMake, tools
from conans.model.version import Version
from conans.errors import ConanInvalidConfiguration

from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment, RunEnvironment, python_requires
from conans.errors import ConanInvalidConfiguration, ConanException
from conans.tools import os_info
import os, re, stat, fnmatch, platform, glob, traceback, shutil
from functools import total_ordering

# if you using python less than 3 use from distutils import strtobool
from distutils.util import strtobool

conan_build_helper = python_requires("conan_build_helper/[~=0.0]@conan/stable")

class LibeventConan(conan_build_helper.CMakePackage):
    name = "libevent"
    description = "libevent - an event notification library"
    topics = ("conan", "libevent", "event")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/libevent/libevent"
    license = "BSD-3-Clause"
    version = "2.1.11"
    exports_sources = ["CMakeLists.txt", "patches/**"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
      "enable_ubsan": [True, False],
      "enable_asan": [True, False],
      "enable_msan": [True, False],
      "enable_tsan": [True, False],
      "shared": [True, False],
      "fPIC": [True, False],
      "with_openssl": [True, False],
      "disable_threads": [True, False]}

    default_options = {
      "enable_ubsan": False,
      "enable_asan": False,
      "enable_msan": False,
      "enable_tsan": False,
      "shared": False,
      "fPIC": True,
      "with_openssl": True,
      "disable_threads": False}

    generators = "cmake", "cmake_find_package"

    # sets cmake variables required to use clang 10 from conan
    def _is_compile_with_llvm_tools_enabled(self):
      return self._environ_option("COMPILE_WITH_LLVM_TOOLS", default = 'false')

    # installs clang 10 from conan
    def _is_llvm_tools_enabled(self):
      return self._environ_option("ENABLE_LLVM_TOOLS", default = 'false')

    _cmake = None
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def configure(self):
        lower_build_type = str(self.settings.build_type).lower()

        if lower_build_type != "release" and not self._is_llvm_tools_enabled():
            self.output.warn('enable llvm_tools for Debug builds')

        if self._is_compile_with_llvm_tools_enabled() and not self._is_llvm_tools_enabled():
            raise ConanInvalidConfiguration("llvm_tools must be enabled")

        if self.options.enable_ubsan \
           or self.options.enable_asan \
           or self.options.enable_msan \
           or self.options.enable_tsan:
            if not self._is_llvm_tools_enabled():
                raise ConanInvalidConfiguration("sanitizers require llvm_tools")

        if self.options.enable_ubsan:
            if self.options.with_openssl:
              self.options["openssl"].enable_ubsan = True

        if self.options.enable_asan:
            if self.options.with_openssl:
              self.options["openssl"].enable_asan = True

        if self.options.enable_msan:
            if self.options.with_openssl:
              self.options["openssl"].enable_msan = True

        if self.options.enable_tsan:
            if self.options.with_openssl:
              self.options["openssl"].enable_tsan = True

        #del self.settings.compiler.libcxx
        #del self.settings.compiler.cppstd

    def build_requirements(self):
        self.build_requires("cmake_platform_detection/master@conan/stable")
        self.build_requires("cmake_build_options/master@conan/stable")
        self.build_requires("cmake_helper_utils/master@conan/stable")

        if self.options.enable_tsan \
            or self.options.enable_msan \
            or self.options.enable_asan \
            or self.options.enable_ubsan:
          self.build_requires("cmake_sanitizers/master@conan/stable")

        # provides clang-tidy, clang-format, IWYU, scan-build, etc.
        if self._is_llvm_tools_enabled():
          self.build_requires("llvm_tools/master@conan/stable")

    def requirements(self):
        # patched
        if self.options.with_openssl:
            self.requires.add("openssl/OpenSSL_1_1_1-stable@conan/stable")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        # temporary fix due to missing files in dist package for 2.1.11, see upstream bug 863
        # for other versions "libevent-{0}-stable".format(self.version) is enough
        extracted_folder = "libevent-release-{0}-stable".format(self.version)
        os.rename(extracted_folder, self._source_subfolder)

    def _patch_sources(self):
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "OPENSSL_INCLUDE_DIR",
                              "OpenSSL_INCLUDE_DIRS")
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "OPENSSL_LIBRARIES",
                              "OpenSSL_LIBRARIES")
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        if self.options.with_openssl:
            self._cmake.definitions["OPENSSL_ROOT_DIR"] = self.deps_cpp_info["openssl"].rootpath
        self._cmake.definitions["EVENT__LIBRARY_TYPE"] = "SHARED" if self.options.shared else "STATIC"
        self._cmake.definitions["EVENT__DISABLE_DEBUG_MODE"] = self.settings.build_type == "Release"
        self._cmake.definitions["EVENT__DISABLE_OPENSSL"] = not self.options.with_openssl
        self._cmake.definitions["EVENT__DISABLE_THREAD_SUPPORT"] = self.options.disable_threads
        self._cmake.definitions["EVENT__DISABLE_BENCHMARK"] = True
        self._cmake.definitions["EVENT__DISABLE_TESTS"] = True
        self._cmake.definitions["EVENT__DISABLE_REGRESS"] = True
        self._cmake.definitions["EVENT__DISABLE_SAMPLES"] = True
        # libevent uses static runtime (MT) for static builds by default
        self._cmake.definitions["EVENT__MSVC_STATIC_RUNTIME"] = self.settings.compiler == "Visual Studio" and \
                self.settings.compiler.runtime == "MT"

        self._cmake.definitions["ENABLE_UBSAN"] = 'ON'
        if not self.options.enable_ubsan:
            self._cmake.definitions["ENABLE_UBSAN"] = 'OFF'

        self._cmake.definitions["ENABLE_ASAN"] = 'ON'
        if not self.options.enable_asan:
            self._cmake.definitions["ENABLE_ASAN"] = 'OFF'

        self._cmake.definitions["ENABLE_MSAN"] = 'ON'
        if not self.options.enable_msan:
            self._cmake.definitions["ENABLE_MSAN"] = 'OFF'

        self._cmake.definitions["ENABLE_TSAN"] = 'ON'
        if not self.options.enable_tsan:
            self._cmake.definitions["ENABLE_TSAN"] = 'OFF'

        self.add_cmake_option(self._cmake, "COMPILE_WITH_LLVM_TOOLS", self._is_compile_with_llvm_tools_enabled())


        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE", src=self._source_subfolder, dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()
        # drop pc and cmake file
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        tools.rmdir(os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.extend(["rt"])

        if self.settings.os == "Windows":
            self.cpp_info.system_libs.append("ws2_32")
            if self.options.with_openssl:
                self.cpp_info.defines.append("EVENT__HAVE_OPENSSL=1")
