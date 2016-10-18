INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_HURDLE1 hurdle1)

FIND_PATH(
    HURDLE1_INCLUDE_DIRS
    NAMES hurdle1/api.h
    HINTS $ENV{HURDLE1_DIR}/include
        ${PC_HURDLE1_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    HURDLE1_LIBRARIES
    NAMES gnuradio-hurdle1
    HINTS $ENV{HURDLE1_DIR}/lib
        ${PC_HURDLE1_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(HURDLE1 DEFAULT_MSG HURDLE1_LIBRARIES HURDLE1_INCLUDE_DIRS)
MARK_AS_ADVANCED(HURDLE1_LIBRARIES HURDLE1_INCLUDE_DIRS)

