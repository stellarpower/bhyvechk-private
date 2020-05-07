#!/usr/bin/python3

# {{{ CDDL HEADER
#
# This file and its contents are supplied under the terms of the
# Common Development and Distribution License ("CDDL"), version 1.0.
# You may only use this file in accordance with the terms of version
# 1.0 of the CDDL.
#
# A full copy of the text of the CDDL should have accompanied this
# source. A copy of the CDDL is also available via the Internet at
# http://www.illumos.org/license/CDDL.
# }}}

# Copyright 2020 OmniOS Community Edition (OmniOSce) Association.

# Work in progress - only works for Intel CPUs

import subprocess, re, sys, csv, platform, os

PLATFORM = platform.system()


from csv_schema.structure.base import BaseCsvStructure
from csv_schema.columns import (
  IntColumn,
  DecimalColumn,
  StringColumn,
)

class FlagCsvStructure(BaseCsvStructure):

   a = StringColumn() # FLAG ID
   b = StringColumn() #FLAG CONSTANT NAME
   c = IntColumn() # FLAG BIT POSITION
   d = StringColumn() # FRIENDLY NAME
   e = IntColumn() # AMD # need to parse as bool
   f = IntColumn() # INTEL # need to parse as bool

def readCSV(file, schemaClass):
     dictRows = csv.DictReader(open(file, newline=''))
     validatedRows = []
     for row in dictRows:
         # validatedRows << schemaClass(row.values(), 1) #the integer is the position: line or column??
         # if not validatedRows[-1].is_valid():
         #     throw some crap here
         validatedRows.append(row)
     return validatedRows
###################################################

import tabulate
from stringcolor import *

def downloadDatabase():
  pass

def contributetoDatabase():
  pass

def getProcessorNameEtc():
  # get any workarounds  or issues form a database
  pass

def addTableRow(test, name, intel, amd, kvmRequired, bhyveRequired):
               #bool test, str name, bool intel, bool amd, bool kvmRequired, bool bhyveRequired): # Link to online resource explaining it
  pass

def msrLoaded():
    if PLATFORM == "Linux":
        return os.WEXITSTATUS(os.system("lsmod | grep -i msr")) == 0
    elif PLATFORM == "SunOS":
        # Fixme - not sure if a kernel module is required, however, only newer illumos has the rdmsr utility
        return os.WEXITSTATUS(os.system("command -v rdmsr")) == 0
    print(cs("Warning: platform-specific detection of availability of `rdmsr` utility not available for htis OS", "magenta"))
    return True #Fallback as above is only a warn, we'll try and have a catch-all later (TODO)



# TODO: Arguably it would be more portable to wrap the C library call to be accessible form Python
# using one of the vaerious methods, because the output from rdmsr differs from system to system.
# However even the C call is non-standard:
# - illumos iuses an ioctl [here](https://github.com/illumos/illumos-gate/blob/9ad2adf3158400d3d79cc126f292aaf481805413/usr/src/cmd/rdmsr/rdmsr.c#L74)
# - NetBSD uses a dedicated [C function](https://netbsd.gw.com/cgi-bin/man-cgi?rdmsr+9+NetBSD-current)
# - It seems the sources for `rdmsr` on linux use the exposed device files. Haven't found
#    a definitve answer yet if it is possible ot use an ioctl in userland. It seems or be
#    inplemented in some manner in the kernel driver.
# Because of this it doesn't seem worth the effort at this time, so we'll just
# switch on the OS to determins the right regular expresion to use.
# An alternative todo would be to expand illumos-gate's `rdmsr` to output the information in a common
# format between the major unixen - for example, implement the `-c` switch used on Linux
def rdmsr(msr, errorMessage = "PLACEHOLDER"):
    if PLATFORM == "Linux":
        command = [ "/usr/sbin/rdmsr", "-x"] #["sudo", "/usr/sbin/rdmsr", "-x"]
    elif PLATFORM == "SunOS":
        command = ["pfexec", "rdmsr"]
    else: #Fallback - attempt lowest common denominator
        command = ["sudo", "rdmsr", "-x"]

    ret = subprocess.run(command + [msr], stdout=subprocess.PIPE, stderr=subprocess.PIPE)#, capture_output=True)
    if ret.returncode != 0:
        print("Failed to check for %s : %s returned %d:\n%s" % (errorMessage, command + [msr], ret.returncode, ret.stdout.decode()))
        # fixme: collect the errors instead and output later
        # fixme :some of these features aren't provided by te CPU,so we ge ta file not found
        return 0
    else:
        m = rdmsr.p.match(ret.stdout.decode())
        if m:
            if PLATFORM == "Linux":
                return int(m.group(0), 16) # FIXME!!
            elif PLATFORM == "SunOS":
                return int(m.group(3), 16)
        return 0 # Throw an exception instead - we shouldn't really get here

rdmsr.p = re.compile(r'((0x[0-9a-f]+): )?(.*)') # I think we've already handled this in the regexp:
#if PLATFORM == "SunOS":
#    rdmsr.p = re.compile(r'((0x[0-9a-f]+): )?(.*)')
#elif PLATFORM == "Linux":
#    rdmsr.p = re.compile(r'((0x[0-9a-f]+): )?(.*)')


#############################

print (cs("bhyvechk - version: " + os.popen("git log --pretty=format:'%h' -n 1").read() + "\n\n", "blue"))


if not msrLoaded():
  print(cs("Error - fix me to output msr aoutput", "red"))
  exit(0)

CSV_DIRECTORY = "."
FLAGS_CSV = CSV_DIRECTORY + "/flags.csv"
SMRS_CSV = CSV_DIRECTORY + "/smrs.csv"
TESTS_CSV = CSV_DIRECTORY + "/tests.csv"

flagRows = None; smrRows = None; testRows = None
try:
    flagRows = readCSV(FLAGS_CSV, FlagCsvStructure)
    smrRows = readCSV(SMRS_CSV, BaseCsvStructure)
    testRows = readCSV(TESTS_CSV, BaseCsvStructure)
except Exception as e:
    print(cs("Error loading required CSV files: %s" % e, "red"))
    exit(10)

smrs = {} ; flags = {}
for row in flagRows:
    flags[row['FLAG ID']] = row
    # parse as boolea thw AMD/INTEL

for row in smrRows:

    smrs[row['RDSMR TEST ID']] = row
    hex = str(row['REGISTER VALUE'])  # keep as string
    try:
        row['RESULT'] = rdmsr(hex)  # int
        row['ERROR'] = None
    except OSError as e:
        row['RESULT'] = cs("ERROR", "red") # str
        row['ERROR'] = e
    # These will be incorporated into dictionary via reference

############
# try:
#     flagRows = csv.DictReader(open(FLAGS_CSV, newline=''))
#     smrRows = csv.DictReader(open(SMRS_CSV, newline=''))
#     testRows = csv.DictReader(open(TESTS_CSV, newline=''))
#     smrs = {} ; flags = {}
#
#     for row in flagRows:
#         flags[row['FLAG ID']] = row
#         # parse as boolea thw AMD/INTEL
#         # can we use a schema and parse properly?
#
# #####
#
#     errorRDSMRS = []
#     errorFlags = []
#
#     try:
#         get rdmsr test from hash
#     except KeyError as e:
#         errorKeys << (key, test ID)
#         print("Error - RDSMR ID %s for test ID %s does not exist in RDSMR database")
#
#     try:
#         get flag bits from hash
#     except KeyError as e:
#         errorFlags << (key, test ID)
#         print("Error - Flag ID %s for test ID %s does not exist in flags database")



####

    # for row in smrRows:
    #     smrs[row['RDSMR TEST ID']] = row
    #     hex = str(row['REGISTER VALUE']) # keep as string
    #     try:
    #         row['RESULT'] = rdmsr(hex) # int
    #         row['ERROR'] = None
    #     except OSError as e:
    #         row['RESULT'] = cs("ERROR", "red")
    #         row['ERROR'] = e

for row in testRows:
    registerValue = smrs[row['rdsmr id']]['RESULT']
    # BIT_MAX_64 = True

    row['RESULT'] = True

    if row['flag id'] != "":
        row['RESULT'] = row['RESULT'] and bool(registerValue & 1 << int(flags[row['flag id']]['FLAG BIT POSITION']))
                                           # 2 ** int(flags[row['flag id']]['FLAG BIT POSITION']))

    if row['Flag 2 id'] != "":
        row['RESULT'] = row['RESULT'] and bool(registerValue & 1 << int(flags[row['Flag 2 id']]['FLAG BIT POSITION']))
                                           #2 ** int(flags[row['Flag 2 id']]['FLAG BIT POSITION']))

print(tabulate.tabulate(testRows, headers = "keys"))


    # if row['flag id'] != "":
    #     flag1 = 2 ** int(flags[row['flag id']]['FLAG BIT POSITION'])
    # else:
    #     flag1 = BIT_MAX_64
    #
    # if row['Flag 2 id'] != "":
    #     flag2 = 2 ** int(flags[row['Flag 2 id']]['FLAG BIT POSITION'])
    # else:
    #     flag2 = BIT_MAX_64

    #row['RESULT'] = (registerValue & flag1) and (registerValue & flag2)



################################################



# def vmx_ctl_one_setting(val, flag):
#     return val & (flag << 32) != 0

# #try:
# i = rdmsr(MSR_IA32_FEAT_CTRL)
#
# if i & IA32_FEAT_CTRL_LOCK and (i & IA32_FEAT_CTRL_VMX_EN) == 0:
#     print("VMX support not enabled in BIOS (essential)")
#     sys.exit()
# else:
#     print("VMX support enabled in BIOS")
# #except OSError as e:
# #    print("Error checking for VMX BIOS Support: ", e)
#
#
# #try:
# i = rdmsr(MSR_IA32_VMX_BASIC)
# if i & IA32_VMX_BASIC_INS_OUTS:
#     print("VMX supports INS/OUTS")
# else:
#     print("VMX does not support INS/OUTS (essential)")
#     sys.exit()
# #except OSError as e:
# #    print("Error checking for VMX INS/OUTS Support: ", e)
#
#
# ctlmsr = (MSR_IA32_VMX_TRUE_PROCBASED_CTLS if (i & IA32_VMX_BASIC_TRUE_CTRLS)
#         else MSR_IA32_VMX_PROCBASED_CTLS)
# i = rdmsr(ctlmsr)
#
# if vmx_ctl_one_setting(i, IA32_VMX_PROCBASED_2ND_CTLS):
#     i = rdmsr(MSR_IA32_VMX_PROCBASED2_CTLS)
#     if vmx_ctl_one_setting(i, IA32_VMX_PROCBASED2_EPT):
#         print("VMX supports EPT")
#         j = rdmsr(MSR_IA32_VMX_EPT_VPID_CAP)
#         if j & IA32_VMX_EPT_VPID_INVEPT:
#             print("VMX supports INVEPT")
#             if j & IA32_VMX_EPT_VPID_INVEPT_SINGLE:
#                 print("VMX supports single INVEPT")
#             if j & IA32_VMX_EPT_VPID_INVEPT_ALL:
#                 print("VMX supports all INVEPT")
#
#     else:
#         print("VMX does not support EPT (optional)")
#     if vmx_ctl_one_setting(i, IA32_VMX_PROCBASED2_VPID):
#         print("VMX supports VPID")
#     else:
#         print("VMX does not support VPID (optional)")

# Vim hints
# vim:ts=4:sw=4:et:fdm=marker
