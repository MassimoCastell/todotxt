@echo off
set ESC=
doskey t=if $1. equ . (todo.py) else todo.py $*
