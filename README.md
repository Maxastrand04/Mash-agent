# Mash agent

A bash command AI agent who lives in your terminal. Exist for the people who are not really comfortable with bash commands and/or the terminal. 

Mash exist to convert a plain english message into a functional bash command!

## Local LLM

Mash uses a local LLM downloaded from `Ollama`. Right now it uses `qwen2.5-coder:7b` model but it should work with any model really. 

The agent takes input from user then uses the local LLM to understand what user wants to do. 
After that it runs through some python scripts to give a consistent and correct bash format as output. 

Example input in a terminal:

```
mash create a new file called bob
```
## Python convertion

In order to ensure the output stays consistent since a tiny local LLM can be very unpredictable it will run through some python scripts. 
These scripts will ensure the formatting of bash command is correct for what user wants to do. 

The python scripts also allows user to add additional information when Mash is in doubt. For example:

```
Where should the new file/folder be created?

  1. destination/to/my/folder  (Current directory)

Select option [1], Enter to cancel, type name for other destination: 1

What file extension?

  1. .md

Select extension [1-1], type one manually (with or without dot), or Enter to cancel: .py
```

## Output

The final output after mash has full picture of what user wants to do is the bash command for doing the task user wants. For example:

```
Run: touch ./bob.py
[y/N]
```

# Why create this?

I am horribly bad at remembering bash commands and to make life easier I wanted a tool to help me remembering.
I feel like a tiny local agent that exist completely on disk with only one task can be very useful both for developers who have not mastered the terminal and beginners who wants help.

## Why not use an agent like claude code? Github copilot? 

Well one reason, API tokens. I do not want to waste my API tokens on a simple task as to find/create/remove files etc. 
This agent can live and run completely locally without ever reaching the internet which also ensures your files and privacy does not leak in to the wrong peoples hands. 

# Project state

As of right now the agent works! it runs locally and needs you to run `ollama serve` in a terminal for it to work. This will change in future scope!

Right now it runs in a `.venv` but that will also be changed for final product.

User preferences is not implemented yet... Final product will let user select model themselves, mash behaviour (unambiguous menus or just output) etc. 

Right now it is a good prototype of the product. 
