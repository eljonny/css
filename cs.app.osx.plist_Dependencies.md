# cs.app.osx.plist Dependencies

These are the dependencies for the cs plist lib.

- cs.logutils
  - cs.ansi_colour>=20200729
    - cs.gimmicks
  - cs.context>=stackable_state
    - cs.deco
      - ...
    - cs.gimmicks
  - cs.deco
    - cs.gimmicks
    - cs.typingutils
  - cs.lex
    - cs.dateutils
    - cs.deco
      - ...
    - cs.gimmicks
    - cs.obj
      - cs.deco
    - cs.pfx
      - ...
    - cs.py.func
    - cs.seq>=20200914
      - cs.deco
        - ...
      - cs.gimmicks
    - python-dateutil
    - icontract
    - typeguard
  - cs.pfx
    - ...
  - cs.py.func
- cs.pfx
  - cs.deco
    - ...
  - cs.py.func>=func_a_kw_fmt
  - cs.py3
  - cs.x
    - cs.ansi_colour
      - ...
    - cs.gimmicks

[//]: # (Added then updated the dependencies list - )
[//]: # (Jonathan Hyry <jonathan.hyry@outlook.com> - 2026-08-15)
