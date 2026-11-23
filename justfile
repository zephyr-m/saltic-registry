set shell := ["bash", "-uc"]
set positional-arguments

# saltic-registry — пакеты Saltic. Язык, полка и craft.testing берутся из дома
# Saltic: SALTIC_HOME, по умолчанию соседняя папка ../saltic.
saltic := env_var_or_default("SALTIC_HOME", justfile_directory() + "/../saltic")
export SALTIC_HOME := saltic
compiler := saltic + "/bootstrap/saltic"

default:
    just --list

# Проверки пакетов (registry/**/checks/*.saltic с program()): собрать родным
# x86-64 и прогнать каждую — программа workbench/check/checks.saltic
checks:
    mkdir -p .cache/build/tools
    {{compiler}} workbench/check/checks.saltic .cache/build/tools/checks 268435456 x86_64
    .cache/build/tools/checks
