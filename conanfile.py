from conans import ConanFile, CMake, tools


class LibeventConan(ConanFile):
    name = "libevent"
    version = "2.1.8"
    license = "BSD"
    url = "https://github.com/libevent/libevent"
    description = "Libevent"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    generators = "cmake"
    requires = "zlib/1.2.11@dostolski/testing","OpenSSL/1.0.2l@dostolski/testing"
    
    def source(self):        
        self.run("git clone {}".format(LibeventConan.url))
        self.run("cd libevent && git checkout -b release-{}-stable release-{}-stable".format(LibeventConan.version, LibeventConan.version))
        tools.replace_in_file("libevent/CMakeLists.txt", "project(libevent C)", '''project(libevent C)
include(${CMAKE_BINARY_DIR}/../conanbuildinfo.cmake)
conan_basic_setup()''')
        tools.replace_in_file("libevent/CMakeLists.txt", '''target_link_libraries(https-client
                    event_extra
                    ${LIB_APPS}
                    ${LIB_PLATFORM})''', '''target_link_libraries(https-client
                    event_extra
                    ${LIB_APPS}
                    ${LIB_PLATFORM}
                    ${CMAKE_DL_LIBS})''')
        tools.replace_in_file("libevent/CMakeLists.txt", '''target_link_libraries(regress
                            ${LIB_APPS}
                            ${LIB_PLATFORM})''', '''target_link_libraries(regress
                            ${LIB_APPS}
                            ${LIB_PLATFORM}
                            ${CMAKE_DL_LIBS})''')
        tools.replace_in_file("libevent/CMakeLists.txt", '''target_link_libraries(${SAMPLE}
                    event_extra
                    ${LIB_APPS}
                    ${LIB_PLATFORM})''', '''target_link_libraries(${SAMPLE}
                    event_extra
                    ${LIB_APPS}
                    ${LIB_PLATFORM}
                    ${CMAKE_DL_LIBS})''')
        
        
    def build(self):
        cmake = CMake(self)
        self.run("mkdir build && cd build && cmake ../libevent %s" % cmake.command_line)
        self.run("cmake --build build %s" % cmake.build_config)

    def package(self):
        header_list = [
            'include/event2/buffer.h',
            'include/event2/buffer_compat.h',
            'include/event2/bufferevent.h',
            'include/event2/bufferevent_compat.h',
            'include/event2/bufferevent_ssl.h',
            'include/event2/bufferevent_struct.h',
            'include/event2/dns.h',
            'include/event2/dns_compat.h',
            'include/event2/dns_struct.h',
            'include/event2/event.h',
            'include/event2/event_compat.h',
            'include/event2/event_struct.h',
            'include/event2/http.h',
            'include/event2/http_compat.h',
            'include/event2/http_struct.h',
            'include/event2/keyvalq_struct.h',
            'include/event2/listener.h',
            'include/event2/rpc.h',
            'include/event2/rpc_compat.h',
            'include/event2/rpc_struct.h',
            'include/event2/tag.h',
            'include/event2/tag_compat.h',
            'include/event2/thread.h',
            'include/event2/util.h',
            'include/event2/visibility.h',
            'include/event2/event-config.h']
        for include_file in header_list:
            self.copy(include_file, dst="", src="libevent")
        self.copy('include/event2/event-config.h', dst="", src="build")
        self.copy("*.h", dst="include", src="src")
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.dylib*", dst="lib", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["event"]
