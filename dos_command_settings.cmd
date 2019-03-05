@echo off
set ESC=
REM doskey t=doskey s=if $1. equ . ("C:\Program Files (x86)\Git\bin\sh.exe" --login) else "C:\Program Files (x86)\Git\bin\sh.exe" --login -c "$*
doskey t=if $1. equ . (todo) else todo $*