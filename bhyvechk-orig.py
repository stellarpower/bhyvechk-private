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

import subprocess, re, sys

MSR_IA32_FEAT_CTRL                  = 0x3a
IA32_FEAT_CTRL_LOCK                 = 1 << 0
IA32_FEAT_CTRL_VMX_EN               = 1 << 2

MSR_IA32_VMX_BASIC                  = 0x480
IA32_VMX_BASIC_INS_OUTS             = 1 << 54
IA32_VMX_BASIC_TRUE_CTRLS           = 1 << 55

MSR_IA32_VMX_TRUE_PROCBASED_CTLS    = 0x48e
MSR_IA32_VMX_PROCBASED_CTLS         = 0x482
IA32_VMX_PROCBASED_2ND_CTLS         = 1 << 31

MSR_IA32_VMX_PROCBASED2_CTLS        = 0x48b
IA32_VMX_PROCBASED2_EPT             = 1 << 1
IA32_VMX_PROCBASED2_VPID            = 1 << 5

MSR_IA32_VMX_EPT_VPID_CAP           = 0x48c
IA32_VMX_EPT_VPID_INVEPT            = 1 << 20
IA32_VMX_EPT_VPID_INVEPT_SINGLE     = 1 << 25
IA32_VMX_EPT_VPID_INVEPT_ALL        = 1 << 26

# def rdmsr(msr):
#     ret = subprocess.run(['/usr/sbin/rdmsr', hex(msr)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)#, capture_output=True)
#     m = rdmsr.p.match(ret.stdout.decode())
#     if m:
#         return int(m.group(2), 16)
#     return 0
# rdmsr.p = re.compile(r'(0x[0-9a-f]+): (.*)')

def rdmsr(msr, errorMessage = "PLACEHOLDER"):
    RDMSR = '/usr/sbin/rdmsr'
    #ESCALATE = '/usr/sbin/rdmsr' # "sudo" #pfexec
    # ESCALATE
    ret = subprocess.run([ RDMSR, '-x', hex(msr)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)#, capture_output=True)
    if ret.returncode != 0:
        print("Failed to check for %s : %s returned %d:\n%s" % (errorMessage, RDMSR, ret.returncode, ret.stdout.decode()))
    else:
        m = rdmsr.p.match(ret.stdout.decode())
        if m:
            return int(m.group(0), 16)
                              #2), 16)
    return 0
rdmsr.p = re.compile(r'((0x[0-9a-f]+): )?(.*)')

def vmx_ctl_one_setting(val, flag):
    return val & (flag << 32) != 0

# Test ID 1
i = rdmsr(MSR_IA32_FEAT_CTRL)
if i & IA32_FEAT_CTRL_LOCK and (i & IA32_FEAT_CTRL_VMX_EN) == 0:
    print("VMX support not enabled in BIOS (essential)")
    sys.exit()
else:
    print("VMX support enabled in BIOS")

# Test ID 2
i = rdmsr(MSR_IA32_VMX_BASIC)
if i & IA32_VMX_BASIC_INS_OUTS:
    print("VMX supports INS/OUTS")
else:
    print("VMX does not support INS/OUTS (essential)")
    sys.exit()

# Test ID 3
ctlmsr = (MSR_IA32_VMX_TRUE_PROCBASED_CTLS if (i & IA32_VMX_BASIC_TRUE_CTRLS)
        else MSR_IA32_VMX_PROCBASED_CTLS)

# Test ID 4,5
i = rdmsr(ctlmsr)

if vmx_ctl_one_setting(i, IA32_VMX_PROCBASED_2ND_CTLS):
    # Test ID 6
    i = rdmsr(MSR_IA32_VMX_PROCBASED2_CTLS)
    if vmx_ctl_one_setting(i, IA32_VMX_PROCBASED2_EPT):
        print("VMX supports EPT")
        # Test ID 7
        j = rdmsr(MSR_IA32_VMX_EPT_VPID_CAP)
        if j & IA32_VMX_EPT_VPID_INVEPT:
            print("VMX supports INVEPT")
            # Test ID 8
            if j & IA32_VMX_EPT_VPID_INVEPT_SINGLE:
                print("VMX supports single INVEPT")
            # Test ID 9
            if j & IA32_VMX_EPT_VPID_INVEPT_ALL:
                print("VMX supports all INVEPT")

    else:
        print("VMX does not support EPT (optional)")
    # Test ID 10
    if vmx_ctl_one_setting(i, IA32_VMX_PROCBASED2_VPID):
        print("VMX supports VPID")
    else:
        print("VMX does not support VPID (optional)")

# Vim hints
# vim:ts=4:sw=4:et:fdm=marker
