# Реестр Saltic

Адаптеры (`registry/adapters/`) и библиотеки (`registry/libraries/`) для
пакетного менеджера tarantul. В Saltic их привозит `just tarantul` по
`tarantul.json` проекта; программы пишут `use tarantul.<пакет>.<модуль>`.

Папка `registry/` внутри — чтобы имена `registry.…` в коде пакетов работали
так же, как когда реестр жил в Saltic; при привозе tarantul переписывает их
на `tarantul.<пакет>`.

## Правка пакета

Строго (решение автора 19.11.2026): изменил код пакета — подними
`own_version` в его паспорте, закоммить и запушь, потом в Saltic
`just tarantul update`. Изменение без новой версии tarantul не примет.

## Проверки

Нужна рабочая копия Saltic рядом (`../saltic`), ядро языка и ОС берутся
из неё через `SALTIC_HOME`:

- сверка адаптеров (паспорт против кода, индекс `registry/adapters/index.json`) —
  из Saltic: `just registry` (сверяет `../saltic-registry`);
- жители UIEngine (этажи и `library.saltic`) — сборщик
  `registry/libraries/uiengine/library/build.saltic`, собирается полкой Saltic
  с `SALTIC_HOME=../saltic` и запускается из корня этого репозитория;
- лимиты канона — `workbench/check/limits-known.txt` (известные нарушения
  файлов реестра).
- проверки пакетов — `just checks`: собирает и гоняет каждую
  `registry/**/checks/*.saltic` с `program()`;
- эталоны проверок — `workbench/references/<пакет>.py`: внешний судья на Python
  считает правильные ответы и пишет их данными в `checks/` пакета. Сам
  Python в пакет не попадает и с ним не уезжает.
- генераторы данных пакетов — `workbench/generators/<пакет>.py` (сейчас —
  глифы `lettering` из `fonts/spleen`); как и эталоны, в пакет не попадают.
