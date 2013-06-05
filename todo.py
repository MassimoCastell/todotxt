# conding: utf-8 
import sys, re
import getopt

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
        #print( "no priotiry" )

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
    -o --origin show origin text
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

    for t in tasks:
        #print( t )
        if not t.isCompleted: 
            print("  " + str(t.id) + ": " +  t.text.strip() )


def edit(filename, numOfLine, newText):
    f = open(filename, "r+")
    lines = f.readlines()
    f.close()

    f = open(filename, "w")
    #print( lines )
    #lines = lines[:numOfLine] + lines[numOfLine+1:]
    try:
        orig = lines[numOfLine-1].strip()
        lines[numOfLine-1] = newText.replace(MAGIC_REPLACE_PLACEHOLDER, orig) + "\n"
        f.writelines(lines)
    except:
        print(str(numOfLine) + " task is not exists")
    finally:
        f.close()


def getThingsDone(filename, numOfLine):
    edit(filename, numOfLine, complete_prefix + " " + MAGIC_REPLACE_PLACEHOLDER)


def handleCommand(command, filename, args):
    if command == "list":
        f = open(filename, "r+")
        list(f.readlines())
        f.close()
    elif command == "add":
        text = " ".join(args)
        f = open(filename, "a+")
        f.write(text+"\n")
        f.close()
        # re-open
        f = open(filename, "r+")
        list(f.readlines())
        f.close()
    elif command == "origin":
        f = open(filename, "r+")
        for line in f:
            print(line.strip())
        f.close()
    elif command == "done":
        if not is_int(args[0]):
            print("Number of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        getThingsDone(filename, numOfLine)
        # re-open
        f = open(filename, "r+")
        list(f.readlines())
        f.close()
    elif command == "edit":
        if not is_int(args[0]):
            print("Number Of line(args0) is not a integer" )
            return
        numOfLine = int(args[0])
        text = " ".join(args[1:])
        edit(filename, numOfLine, text)
        # re-open
        f = open(filename, "r+")
        list(f.readlines())
        f.close()
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
        opts, args = getopt.getopt(argv, "a:hloi:", ["add=", "help", "list", "origin", "input="]) 
    except getopt.GetoptError:           
        usage()                          
        sys.exit(2)  

    _filename = "todo.txt"
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
        elif opt in ("-o", "--origin"):
            command = "origin"

        if opt in ("-i", "--input"):
            _filename = arg

    handleCommand(command, _filename, _text)

    while True:
        command = input(":")
        tmp = command.split(" ")
        command = tmp[0]
        args = tmp[1:]
        if command == "exit":
            sys.exit()
        handleCommand(command, _filename, args)




if __name__ == "__main__":
    main(sys.argv[1:])
