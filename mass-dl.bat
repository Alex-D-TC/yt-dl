
@echo %1

@set out_path=%1
@shift

:loop
python main.py -yt_id %1 -out_path %out_path%
@shift
@if not "%~1"=="" goto loop

