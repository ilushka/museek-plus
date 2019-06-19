#!/bin/bash

BIN_NAME=$(basename $0)

function show_usage() {
    case $1 in
        "install-env")
            printf "Install virtualenv and install python-bindings into it.\n"
            ;;
        "start")
            printf "Start backend application.\n"
            ;;
        "pylint")
            printf "Run pylint on all Python code.\n"
            ;;
        *)
            printf "Usage: ${BIN_NAME} <"
            cat ${BIN_NAME} | awk 'BEGIN { FS = "\""; ORS = "|"; } /\"[a-z\-]+\"\) # first-level-arg/ { print $2; }'
            printf "\b>\n"
            ;;
    esac
}

function install_env() {
    virtualenv pyenv
    . pyenv/bin/activate
    pip install Flask
    pushd ../../python-bindings
    python setup.py build
    python setup.py install
    popd
    pushd ../../Mucipher/PyMucipher
    python setup.py build
    python setup.py install
    popd
}

function start_app {
    . pyenv/bin/activate
    python museekwebui.py
}

function do_pylint {
    . pyenv/bin/activate
    printf "mudriver.py:\n\n"
    pylint mudriver.py
    printf "kvring.py:\n\n"
    pylint kvring.py
}

case $1 in
    "install-env") # first-level-arg;
        install_env "${@:2}"
        ;;
    "start") # first-level-arg;
        start_app "${@:2}"
        ;;
    "pylint") # first-level-arg;
        do_pylint "${@:2}"
        ;;
    "help") # first-level-arg;
        show_usage "${@:2}"
        ;;
    *)
        show_usage "${@:2}"
        ;;
esac

