# About

Modified `libevent` recipe

## EXTRA FEATURES

- supports "openssl/OpenSSL_1_1_1-stable@conan/stable"

# About

## Docker build

```bash
export MY_IP=$(ip route get 8.8.8.8 | sed -n '/src/{s/.*src *\([^ ]*\).*/\1/p;q}')
sudo -E docker build \
    --build-arg PKG_NAME=libevent/2.1.8 \
    --build-arg PKG_CHANNEL=dev/stable \
    --build-arg PKG_UPLOAD_NAME=libevent/2.1.8@dev/stable \
    --build-arg CONAN_EXTRA_REPOS="conan-local http://$MY_IP:8081/artifactory/api/conan/conan False" \
    --build-arg CONAN_EXTRA_REPOS_USER="user -p password1 -r conan-local admin" \
    --build-arg CONAN_INSTALL="conan install --profile clang --build missing" \
    --build-arg CONAN_CREATE="conan create --profile clang --build missing" \
    --build-arg CONAN_UPLOAD="conan upload --all -r=conan-local -c --retry 3 --retry-wait 10 --force" \
    --build-arg BUILD_TYPE=Debug \
    -f conan_libevent.Dockerfile --tag conan_libevent . --no-cache
```

## Local build

```bash
export PKG_NAME=libevent/2.1.8@dev/stable
conan remove --force $PKG_NAME
conan create . dev/stable -s build_type=Debug --profile clang --build missing
CONAN_REVISIONS_ENABLED=1 CONAN_VERBOSE_TRACEBACK=1 CONAN_PRINT_RUN_COMMANDS=1 CONAN_LOGGING_LEVEL=10 conan upload $PKG_NAME --all -r=conan-local -c --retry 3 --retry-wait 10 --force
```

## How to diagnose errors in conanfile (CONAN_PRINT_RUN_COMMANDS)

```bash
# NOTE: about `--keep-source` see https://bincrafters.github.io/2018/02/27/Updated-Conan-Package-Flow-1.1/
CONAN_REVISIONS_ENABLED=1 CONAN_VERBOSE_TRACEBACK=1 CONAN_PRINT_RUN_COMMANDS=1 CONAN_LOGGING_LEVEL=10 conan create . conan/stable -s build_type=Debug --profile clang --build missing --keep-source
```
