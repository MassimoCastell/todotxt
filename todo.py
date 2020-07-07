# coding: cp1252
import sys, re, os
import getopt
import win32console
from colorama import init, Fore, Back, Style
import configparser
import datetime
import win32com.client

# # connect to outlook tasks
# try:
#     outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
#     if (outlook):
#         todo_folder = outlook.GetDefaultFolder(13)
#         todo_items = todo_folder.Items
# except:
#     pass

# use Colorama
init()
taskcolorlist = [(33,"YELLOW"), (32,"GREEN"), (36,"CYAN"), (37,"WHITE")]
colorlist = [(30,"BLACK"), (31,"RED"), (32,"GREEN"), (33,"YELLOW"), (34,"BLUE"), (35,"MAGENTA"), (36,"CYAN"), (37,"WHITE")]

config = configparser.ConfigParser()
if os.path.isfile(str(os.environ['USERPROFILE'])+'\\todotxt.ini'):
    config.read(str(os.environ['USERPROFILE'])+'\\todotxt.ini')
else:
    os.chdir(os.path.dirname(__file__))
    wrkdir = os.getcwd()
    config.read(str(wrkdir)+'\\todotxt.ini')

todofile = config['files']['todofile']
donefile = config['files']['donefile']

DEBUG = True
NONE_PRIORITY = "z" # lowercase "z" because sorting

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
        self.prioritystring = ""
        self.perpendedDate = None
        self.projects = []
        # set projekt color magenta
        self.projectscolor = 35
        self.contexts = []
        # set context color red
        self.contextscolor = 31
        self.isCompleted = False
        self.completedDate = None
        self.taskContent = None
        # set default color to 4th element of taskcolorlist because tasks with prio rotate through the first 3 colors
        self.color = 3
        self.outlookid = ""
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
    + ", outlookid=" + str(self.outlookid)


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
        task.prioritystring = "("+task.priority+")"
        rest = rest.replace(match, "")
        # rotate through the 3 elements of the taskcolorlist. Using ascii code and modulo operator
        # if more colors are wished the "62" and the divisor should be adjusted
        task.color = (ord(task.priority)-62) % 3
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
    print( """USAGE: todo.py <command> <taskid> <text>
    Without options starts the editor mode.

    options:

    h or help                   show help info
    q or quit or exit           quit the editor mode
    a or add                    add a new task
    ls or list <text>           list all tasks(sorted by prio). <Text> Searchtext. if only one character the prio.
    dls or donelist <text>      list all done tasks(sorted by completed date). <Text> Searchtext
    d or do or done <id>        marks task as done
    e or edit <id>              edit text of task
    del or delete <id>          deletes task
    + or project <id> <text>    add project flag to task
    @ or context <id> <text>    add context flag to task
    p or prio <id> <letter>     set priority of task. Empty <letter> deletes prio from <id>
                                if <letter> is "+" or "-" it increase/decrease prio
    o or open <id>              if a URL is in the task, it will be opend in Firefox New Tab
    archive                     move all done task to the done.txt defined in the ini file
    clean                       deletes all task
    """ )
        
def SortTaskPrio(lines):
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
    completedTasks = sorted(completedTasks, key=lambda task: task.completedDate, reverse=True)   # sort by completedDate

    tasks = todoTasks + completedTasks
    return(tasks)

def list(lines, searchstr):
    taskssorted = SortTaskPrio(lines)
    if searchstr:
        searchstr = searchstr[0].lower()
        if len(searchstr) == 1:
            searchstr = str("(")+searchstr+str(")")
    else:
        searchstr = ""
    for t in taskssorted:
        #print( t )
        if not t.isCompleted:
            if searchstr in str(t.text).lower():
                # print('\033[;1;'+str(color)+'m' + "{:02}: {}".format(t.id, t.text.strip()) + "\033[;0;0m")
                tprojects = ""
                if t.projects:
                    for x in t.projects:
                        tprojects = tprojects+" "+str("+"+str(x))
                tcontexts = ""
                if t.contexts:
                    for x in t.contexts:
                        tcontexts = tcontexts+" "+str("@"+str(x))
                tpriority = ""
                if t.prioritystring:
                    tpriority = t.prioritystring+" "
                print('\033[;1;'+str(taskcolorlist[t.color][0])+'m' + "{:02}: ".format(t.id)+ tpriority + t.textContent.strip() + '\033[;0;0m'+
                    '\033[;1;'+str(t.projectscolor)+'m' + "{}".format(tprojects)+
                    '\033[;1;'+str(t.contextscolor)+'m' + "{}".format(tcontexts)+
                    '\033[;0;0m')

def donelist(lines, searchstr):
    taskssorted = SortTaskPrio(lines)
    if searchstr:
        searchstr = searchstr[0].lower()
    else:
        searchstr = ""
    for t in taskssorted:
        #print( t )
        if t.isCompleted:
            if searchstr in str(t.text).lower():
                # print('\033[;1;'+str(color)+'m' + "{:02}: {}".format(t.id, t.text.strip()) + "\033[;0;0m")
                tprojects = ""
                if t.projects:
                    for x in t.projects:
                        tprojects = tprojects+" "+str("+"+str(x))
                tcontexts = ""
                if t.contexts:
                    for x in t.contexts:
                        tcontexts = tcontexts+" "+str("@"+str(x))
                tpriority = ""
                if t.prioritystring:
                    tpriority = t.prioritystring+" "
                # all done tasks printet cyan
                print('\033[;1;36m' + "{:02}: ".format(t.id) + t.completedDate +" "+ tpriority + t.textContent.strip() + '\033[;0;0m'+
                    '\033[;1;'+str(t.projectscolor)+'m' + "{}".format(tprojects)+
                    '\033[;1;'+str(t.contextscolor)+'m' + "{}".format(tcontexts)+
                    '\033[;0;0m')

def edit(filename, numOfLine):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "w")
    #print( lines )
    # lines = lines[:numOfLine] + lines[numOfLine+1:]
    try:
        orig = lines[numOfLine-1].strip()
        newtxt = input_def("EDIT: ", orig)
        lines[numOfLine-1] = newtxt + "\n"
    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.writelines(lines)
        f.close()

def deleteTask(filename, numOfLine):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "w")
    try:
        lines.remove(lines[numOfLine-1])
    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.writelines(lines)
        f.close()
    
    # handleCommand("clear", filename, "")
    # handleCommand("list", filename, "")

def archiveTasks(filename):
    global donefile
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()
    taskssorted = SortTaskPrio(lines)
    to_delete = []
    for t in taskssorted:
        if t.isCompleted:
            tid = str("{}".format(t.id))
            to_delete.append(int(tid))
            f = open(donefile, "a+", encoding='cp1252')
            f.write(t.text)
            f.close()
    # delete done tasks in reversed order because autmatic resort of the list index
    to_delete.sort(reverse = True)
    for numOfLine in to_delete:
        lines.remove(lines[numOfLine-1])
    f = open(filename, "w")
    f.writelines(lines)
    f.close()
    handleCommand("clear", todofile, "")
    handleCommand("list", todofile, "")

def handlePrefix(filename, command, numOfLine, prio=""):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "w")
    try:
        orig = lines[numOfLine-1].strip()
        if command == "done":
            now = datetime.datetime.now()
            donedate = now.strftime("%Y-%m-%d")
            newtxt = str(complete_prefix)+" "+str(donedate)+" "+str(orig)
            lines[numOfLine-1] = newtxt + "\n"
        elif command == "prio":
            m = re.search(priority_reg, orig)
            if m is not None:
                if prio == "empty":
                    newtxt = orig[4:]
                    lines[numOfLine-1] = newtxt + "\n"
                elif prio == "+":
                    origprio = orig[:3]
                    origprio = origprio.strip().replace("(", "").replace(")", "")
                    orignoprio = orig[4:]
                    prio = origprio.upper()
                    if origprio == "A":
                        prio = "A"
                    else:
                        prio = chr(ord(origprio)-1)
                    newtxt = "("+str(prio).upper()+") "+str(orignoprio)
                    lines[numOfLine-1] = newtxt + "\n"
                elif prio == "-":
                    origprio = orig[:3]
                    origprio = origprio.strip().replace("(", "").replace(")", "")
                    orignoprio = orig[4:]
                    prio = origprio.upper()
                    if origprio == "Z":
                        prio = "Z"
                    else:
                        prio = chr(ord(origprio)+1)
                    newtxt = "("+str(prio).upper()+") "+str(orignoprio)
                    lines[numOfLine-1] = newtxt + "\n"

                else:
                    orignoprio = orig[4:]
                    newtxt = "("+str(prio).upper()+") "+str(orignoprio)
                    lines[numOfLine-1] = newtxt + "\n"
            else:
                if prio.isalpha():
                    newtxt = "("+str(prio).upper()+") "+str(orig)
                    lines[numOfLine-1] = newtxt + "\n"
                else:
                    newtxt = orig[:3]
                    lines[numOfLine-1] = newtxt + "\n"

    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.writelines(lines)
        f.close()
    
    # handleCommand("clear", filename, "")
    # handleCommand("list", filename, "")

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
    
    # handleCommand("clear", filename, "")
    # handleCommand("list", filename, "")

def openurl(filename, numOfLine):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "r+")
    try:
        line = lines[numOfLine-1].strip()
        urltxt = re.search(r"(http|https|ftp|ftps):\/\/[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,3}(\/\S*)?", line)
        if urltxt is not None:
            url = urltxt.group(0)
            # os.startfile(url)
            os.spawnl(os.P_NOWAIT, r'C:\Program Files\Mozilla Firefox\Firefox.exe', r'FireFox', '-new-tab', url)
        else:
            print("no URL in task")
    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.close()

    # handleCommand("clear", filename, "")
    # handleCommand("list", filename, "")


def handleCommand(command, filename, args):
    if command == "list" or command[:2] == "ls":
        if command[:2] == "ls" and len(command) == 3:
            args = command[2]
        else:
            args = args
        handleCommand("clear", filename, "")
        f = open(filename, "r+")
        list(f.readlines(), args)
        f.close()
    elif command == "donelist" or command == "dls":
        handleCommand("clear", filename, "")
        f = open(filename, "r+")
        donelist(f.readlines(), args)
        f.close()
    elif command == "add" or command == "a":
        text = " ".join(args)
        f = open(filename, "a+")
        f.write(text+"\n")
        f.close()
        handleCommand("clear", filename, "")
        handleCommand("list", filename, "")
    elif command == "done" or command == "do" or command == "d":
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        handlePrefix(filename, "done", numOfLine)
    elif command == "edit" or command == "e":
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number Of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        edit(filename, numOfLine)
    elif command == "delete" or command == "del":
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        deleteTask(filename, numOfLine)
    elif command == "+" or command == "@"  or command == "project" or command == "context":
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
        if len(args) > 1:
            flag_text = str(args[1])
            addFlag(filename, command, numOfLine, flag_text)
        else:
            prio = "No project or context given"
    elif command == "prio" or command == "p":
        # print("set prio")
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        if len(args) > 1:
            prio = str(args[1])
        else:
            prio = "empty"
        handlePrefix(filename, "prio", numOfLine, prio)
    elif command == "open" or command == "o":
        if not args:
            print("No line number given")
            return
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        openurl(filename, numOfLine)
    elif command == "vim":
        os.system(r'vim '+str(filename))
        # os.spawnl(os.P_NOWAIT, r'C:\Program Files (x86)\Vim\vim82\vim.exe', r'vim', filename)
        # os.startfile(url)
        # os.spawnl(os.P_NOWAIT, r'C:\Program Files\Mozilla Firefox\Firefox.exe', r'FireFox', '-new-tab', url)
        # openurl(filename, numOfLine)
    elif command == "clean":
        confirm = input("Are you sure? It will delete ALL Tasks! [Y/N]: ")
        if confirm == "Y":
            f = open(filename, "w")
            # delete all lines
            f.close()
    elif command == "archive":
        archiveTasks(filename)
    elif command == "clear":
        # print( "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n" )
        print('\033[2J')
    elif command == "help" or command == "h":
        usage()
    else:
        print("Can't find command: %s " % command)
        usage()


def main(argv):

    if argv:
        cmdcommand = argv[0]
        cmdtext = argv[1:]
    else:
        cmdcommand = ""
        cmdtext = ""

    if cmdcommand:
        handleCommand(cmdcommand, todofile, cmdtext)
        sys.exit()

    handleCommand("clear", todofile, "")
    handleCommand("list", todofile, "")

    while True:
        command = input(":")
        tmp = command.split(" ")
        command = tmp[0]
        args = tmp[1:]
        if (command == "exit") or (command == "quit") or (command == "q"):
            sys.exit()
        handleCommand(command, todofile, args)


if __name__ == "__main__":
    main(sys.argv[1:])
