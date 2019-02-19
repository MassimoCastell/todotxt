# -*- coding: utf-8 -*-
import sys, re
import getopt
import win32console
from colorama import init, Fore, Back, Style
import configparser

# use Colorama
init()
colorlist = [(30,"BLACK"), (31,"RED"), (32,"GREEN"), (33,"YELLOW"), (34,"BLUE"), (35,"MAGENTA"), (36,"CYAN"), (37,"WHITE")]

DEBUG = True
NONE_PRIORITY = "z" # 默认优先级
MAGIC_REPLACE_PLACEHOLDER = "%" # edit模式下代替原本文字

complete_reg = r"^x "
complete_prefix = "x"
priority_reg = r"^\([A-Z]\) "
date_reg = r"^[0-9]{4}-[0-9]{2}-[0-9]{2} "
project_reg = r"\+[^ ]+ {0,1}"
project_prefix = "+"
context_reg = r"@[^ ]+ {0,1}"
context_prefix = "@"

# To be able to edit the input line
_stdin = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)

def input_def(prompt, default=''):
    keys = []
    # for c in unicode(default):
    for c in default:
        evt = win32console.PyINPUT_RECORDType(win32console.KEY_EVENT)
        evt.Char = (c)
        evt.RepeatCount = 1
        evt.KeyDown = True
        keys.append(evt)

    _stdin.WriteConsoleInput(keys)
    # return raw_input(prompt)
    return input(prompt)

def is_int(str):
    try:
        int(str)
        return True
    except ValueError:
        return False

class Task:
    def __init__(self, text):
        self.text = text
        self.priority = NONE_PRIORITY
        self.perpendedDate = None
        self.projects = []
        self.contexts = []
        self.isCompleted = False
        self.completedDate = None
        self.taskContent = None
        self.id = 0

    def __str__(self):
        return "#obj Task (" \
    + "  isCompleted=" + str(self.isCompleted) \
    + ", completedDate=" + str(self.completedDate) \
    + ", priority=" + str(self.priority) \
    + ", perpendedDate=" + str(self.perpendedDate) \
    + ", projects=" + str(self.projects) \
    + ", contexts=" + str(self.contexts) \
    + ", taskContent=" + str(self.taskContent) \
    + ""


def parseTask(text):
    rest = text

    task = Task(text)

    # -- Complete Tasks: 2 Format Rules --

    # Rule 1: A completed task starts with an x.
    m = re.search(complete_reg, rest)
    if m is not None:
        match = m.group(0)
        task.isCompleted = True
        rest = rest.replace(match, "")
    #else:
        #print( "not complete" )

    if task.isCompleted:
        m = re.search(date_reg, rest)
        if m is not None:
            match = m.group(0)
            task.completedDate = match.strip().replace("(", "").replace(")", "")
            rest = rest.replace(match, "")
        #else:
        #   print( "no date" )


    # -- Incomplete Tasks: 3 Format Rules --

    # Rule 1: If priority exists, it ALWAYS appears first.
    m = re.search(priority_reg, rest)
    if m is not None:
        match = m.group(0)
        task.priority = match.strip().replace("(", "").replace(")", "")
        rest = rest.replace(match, "")
    #else:
        #print( "no priority" )

    # Rule 2: A task’s creation date may optionally appear directly after priority and a space.
    m = re.search(date_reg, rest)
    if m is not None:
        match = m.group(0)
        task.prependedDate = match.strip().replace("(", "").replace(")", "")
        rest = rest.replace(match, "")
    #else:
        #print( "no date" )

    # Rule 3: Contexts and Projects may appear anywhere in the line after priority/prepended date.
    m = re.findall(project_reg, rest)
    for item in m:
        rest = rest.replace(item, "")
        item = item.strip().replace(project_prefix, "")
        task.projects.append( item )

    m = re.findall(context_reg, rest)
    for item in m:
        rest = rest.replace(item, "")
        item = item.strip().replace(context_prefix, "")
        task.contexts.append( item )

    task.textContent = rest.strip()
    return task

def usage():
    print( """USAGE: todo.py -a yourtask

    options:

    -h --help show help info
    -a --add add a new task
    -l --list list all tasks(sorted)
    -i --input input text file name
    """ )
        

def list(lines):
    todoTasks = []
    completedTasks = []

    numOfLine = 1
    for line in lines:
        if line:
            task = parseTask( line ) 
            task.id = numOfLine
            #print( task )
            if not task.isCompleted:
                todoTasks.append(task)
            else:
                completedTasks.append(task)
        numOfLine += 1

    todoTasks = sorted(todoTasks, key=lambda task: task.priority)   # sort by priority
    #completedTasks = sorted(completedTasks, key=lambda task: task.completedDate, reverse=True)   # sort by completedDate

    tasks = todoTasks + completedTasks

    color = 31
    for t in tasks:
        #print( t )
        if not t.isCompleted: 
            print('\033[;1;'+str(color)+'m' + "{:02}: {}".format(t.id, t.text.strip()) + "\033[;0;0m")
            color += 1
            if color > 37:
                color = 31


def edit(filename, numOfLine):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "w")
    #print( lines )
    # lines = lines[:numOfLine] + lines[numOfLine+1:]
    try:
        orig = lines[numOfLine-1].strip()
        # input(orig)
        newtxt = input_def("EDIT: ", orig)
        # lines[numOfLine-1] = newText.replace(MAGIC_REPLACE_PLACEHOLDER, newtxt) + "\n"
        lines[numOfLine-1] = newtxt + "\n"
        f.writelines(lines)
    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.close()


def getThingsDone(filename, numOfLine):
    edit(filename, numOfLine, complete_prefix + " " + MAGIC_REPLACE_PLACEHOLDER)

def deleteTask(filename, numOfLine):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "w")
    try:
        lines.remove(lines[numOfLine-1])
        f.writelines(lines)
    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.close()
    
    handleCommand("clear", filename, "")
    handleCommand("list", filename, "")

def handlePrefix(filename, command, numOfLine, prio=""):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "w")
    try:
        orig = lines[numOfLine-1].strip()
        if command == "done":
            newtxt = str(complete_prefix)+" "+str(orig)
            lines[numOfLine-1] = newtxt + "\n"
        elif command == "prio":
            m = re.search(priority_reg, orig)
            if m is not None:
                orignoprio = orig[4:]
                newtxt = "("+str(prio).upper()+") "+str(orignoprio)
                lines[numOfLine-1] = newtxt + "\n"
            else:
                newtxt = "("+str(prio).upper()+") "+str(orig)
                lines[numOfLine-1] = newtxt + "\n"
        f.writelines(lines)
    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.close()
    
    handleCommand("clear", filename, "")
    handleCommand("list", filename, "")

def addFlag(filename, command, numOfLine, flag_text):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "w")
    try:
        orig = lines[numOfLine-1].strip()
        newtxt = str(orig)+" "+str(command)+str(flag_text)
        lines[numOfLine-1] = newtxt + "\n"
        f.writelines(lines)
    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.close()
    
    handleCommand("clear", filename, "")
    handleCommand("list", filename, "")

def handleCommand(command, filename, args):
    if command == "list" or command == "l":
        f = open(filename, "r+")
        list(f.readlines())
        f.close()
    elif command == "add" or command == "a":
        text = " ".join(args)
        f = open(filename, "a+")
        f.write(text+"\n")
        f.close()
        # re-open
        f = open(filename, "r+")
        list(f.readlines())
        f.close()
    elif command == "done" or command == "x":
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        handlePrefix(filename, "done", numOfLine)
        # re-open
        f = open(filename, "r+")
        list(f.readlines())
        f.close()
    elif command == "edit" or command == "e":
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number Of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        # text = " ".join(args[1:])
        edit(filename, numOfLine)
        # re-open
        # f = open(filename, "r+")
        # list(f.readlines())
        # f.close()
    elif command == "delete" or command == "d":
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        deleteTask(filename, numOfLine)
    elif command == "+" or command == "@"  or command == "project" or command == "context" or command == "p" or command == "c":
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        if command == "+" or command == "project" or command == "p":
            command = "+"
        if command == "@" or command == "context" or command == "c":
            command = "@"
        numOfLine = int(args[0])
        flag_text = str(args[1])
        addFlag(filename, command, numOfLine, flag_text)
    elif command == "prio" or command == "i":
        print("set prio")
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        prio = str(args[1])
        handlePrefix(filename, "prio", numOfLine, prio)
    elif command == "clean":
        confirm = input("Are you sure? It will delete ALL Tasks! [Y/N]: ")
        if confirm == "Y":
            f = open(filename, "w")
            # delete all lines
            f.close()
    elif command == "clear":
        print( "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n" )
    else:
        print("Cann't found command: %s " % command)


def main(argv):
    try:                                
        opts, args = getopt.getopt(argv, "a:hloi:", ["add=", "help", "list", "input="]) 
    except getopt.GetoptError:           
        usage()                          
        sys.exit(2)  

    config = configparser.ConfigParser()
    config.read('todo.ini')

    _filename = config['files']['todofile']
    print(_filename)
    _text = None

    command = "list"

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()                          
            sys.exit()  
        elif opt in ("-a", "--add"):
            command = "add"
            _text = arg
        elif opt in ("-l", "--list"):
            command = "list"

        if opt in ("-i", "--input"):
            _filename = arg

    handleCommand(command, _filename, _text)

    while True:
        command = input(":")
        tmp = command.split(" ")
        command = tmp[0]
        args = tmp[1:]
        if (command == "exit") or (command == "quit") or (command == "q"):
            sys.exit()
        handleCommand(command, _filename, args)




if __name__ == "__main__":
    main(sys.argv[1:])
