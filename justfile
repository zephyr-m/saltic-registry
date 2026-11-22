set shell := ["bash", "-uc"]
set positional-arguments

# saltic-registry — пакеты Saltic. Язык, полка и craft.testing берутся из дома
# Saltic: SALTIC_HOME, по умолчанию соседняя папка ../saltic.
saltic := env_var_or_default("SALTIC_HOME", justfile_directory() + "/../saltic")
export SALTIC_HOME := saltic
compiler := saltic + "/bootstrap/saltic"

default:
    just --list

# Проверки пакетов (registry/**/checks/*.saltic): собрать родным x86-64 и прогнать каждую
checks:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p .cache/build/checks
    for f in $(git ls-files 'registry/*/checks/*.saltic'); do
        name=$(echo "$f" | tr '/' '_' | sed 's/\.saltic$//')
        echo "== $f"
        {{compiler}} "$f" ".cache/build/checks/$name" 268435456 x86_64 > ".cache/build/checks/$name.log" 2>&1 || { tail -5 ".cache/build/checks/$name.log"; exit 1; }
        ".cache/build/checks/$name"
    done
