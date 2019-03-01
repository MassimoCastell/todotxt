# ToDoTxt Windows CLI

Implemented in Python using colorama and pywin32 module

Based on Gina Trapani's ToDo list format in a simple text file.
You can read all about it [here](https://github.com/ginatrapani/todo.txt-cli/wiki/The-Todo.txt-Format).

More Information, mobile apps and graphical UIs on the [website](http://todotxt.com/).

## **Installation**
* Be sure that Python is installed and in the PATH Variable.
* Download all the files
* Install the required modules with
```elm
pip install -r requirements.txt
```
* Set the PATH Variable to the Folder where the todo.py is stored. Now you can use it from every "folder" in the command shell.
* It's possible to locate the **todotxt.ini** in your User profile %USERPROFILE%.


## **Troubleshooting**

**Windows 10**
Some Python installation under Windows 10 can't forward more than one option in the command line.
If you have errors adding a new task, you installation has this error.
Please import the **win10_python_todotxt.reg** to your registry by double click at it will be fixed.
