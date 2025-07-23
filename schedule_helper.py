import sys
import os
import platform
import click

def get_python_exec():
    return sys.executable

@click.command()
@click.option('--time', prompt='Time (24h, e.g. 14:30)', help='Time to send the email')
@click.option('--args', prompt='CLI arguments', help='Arguments for main.py (e.g. --to x --subject y ...)')
def schedule(time, args):
    py_exec = get_python_exec()
    main_path = os.path.abspath('main.py')
    if platform.system() == 'Windows':
        hour, minute = time.split(':')
        cmd = f'{py_exec} {main_path} {args}'
        sch = f'SchTasks /Create /SC DAILY /TN "EmailAutomation" /TR "{cmd}" /ST {hour}:{minute}'
        print('Windows Task Scheduler command:')
        print(sch)
    else:
        hour, minute = time.split(':')
        cmd = f'{py_exec} {main_path} {args}'
        cron = f'{minute} {hour} * * * {cmd}'
        print('Cron job line:')
        print(cron)

if __name__ == '__main__':
    schedule() 