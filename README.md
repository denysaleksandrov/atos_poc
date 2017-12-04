# atos_poc
Couple of scripts used to automate ATOS EVPN/VXLAN DC setup.

Provision using Python script
-----------------------------

Type5 EVPN tenant, 2 VNIs starting from 110

```
./add_evpn.py templates/devices evpn -nv 2 -vid 110
[edit interfaces ae1 unit 0 family ethernet-switching vlan]
-       members [ 103 200-201 v100 v101 ];
+       members [ 103 110-111 200-201 v100 v101 ];
[edit interfaces irb]
+    unit 110 {
+        family inet {
+            address 100.0.110.1/24;
+        }
+        mac 00:00:00:00:11:00;
+    }
+    unit 111 {
+        family inet {
+            address 100.0.111.1/24;
+        }
+        mac 00:00:00:00:11:10;
+    }
...
Done
...
Done
...
Done
...
Done
```

Type2 EVPN tenant, 2 VNIs starting from 110
```
./add_evpn.py templates/devices evpn -t Type2 -nv 2 -vid 110
```

Rolling back if needed
```
./rollback.py templates/devices                                                                                                                  
qfx5110-3 - Done
qfx5110-4 - Done
qfx5110-5 - Done
qfx5110-6 - Done
```

Provision using Ansible
-----------------------

```
ansible-playbook pb.do_evpn.yml --diff -e "type=Type2"                                                                       

PLAY [Create config for leaf] **************************************************

TASK [include_vars] ************************************************************
ok: [qfx5110-6]
ok: [qfx5110-3]
ok: [qfx5110-5]
ok: [qfx5110-4]

TASK [vlans : create vlans] ****************************************************
ok: [qfx5110-6]
ok: [qfx5110-3]
ok: [qfx5110-5]
ok: [qfx5110-4]

TASK [policy : create policy] **************************************************
ok: [qfx5110-5]
ok: [qfx5110-4]
ok: [qfx5110-6]
ok: [qfx5110-3]

TASK [evpn : create evpn] ******************************************************
ok: [qfx5110-5]
ok: [qfx5110-3]
ok: [qfx5110-4]
ok: [qfx5110-6]

TASK [interfaces : create interfaces] ******************************************
ok: [qfx5110-3]
ok: [qfx5110-4]
ok: [qfx5110-6]
ok: [qfx5110-5]

TASK [routing-instances : create vlans] ****************************************
ok: [qfx5110-6]
ok: [qfx5110-3]
ok: [qfx5110-5]
ok: [qfx5110-4]

TASK [build-config : Assembling configurations and copying to conf/] ***********
ok: [qfx5110-3]
ok: [qfx5110-4]
ok: [qfx5110-6]
ok: [qfx5110-5]

PLAY [add vxlan] ***************************************************************

TASK [include_vars] ************************************************************
ok: [qfx5110-3]
ok: [qfx5110-4]
ok: [qfx5110-5]
ok: [qfx5110-6]

TASK [delete default term in EVPN-host-routes policy] **************************

[edit policy-options policy-statement EVPN-host-routes]
-    term default {
-        then reject;
-    }
changed: [qfx5110-4]

[edit policy-options policy-statement EVPN-host-routes]
-    term default {
-        then reject;
-    }
changed: [qfx5110-6]

[edit policy-options policy-statement EVPN-host-routes]
-    term default {
-        then reject;
-    }
changed: [qfx5110-5]

[edit policy-options policy-statement EVPN-host-routes]
-    term default {
-        then reject;
-    }
changed: [qfx5110-3]

TASK [add config] **************************************************************

[edit interfaces ae1 unit 0 family ethernet-switching vlan]
-       members [ 103 200-201 v100 v101 ];
+       members [ 103 110-111 200-201 v100 v101 ];
[edit interfaces ae2 unit 0 family ethernet-switching vlan]
-       members v203;
+       members [ 110-111 v203 ];
[edit interfaces irb]
+    unit 110 {
+        family inet {
+            address 100.0.110.1/24;
+        }
+        mac 00:00:00:00:11:00;
+    }
+    unit 111 {
+        family inet {
+            address 100.0.111.1/24;
+        }
+        mac 00:00:00:00:11:10;
+    }
[edit protocols evpn vni-options]
+     vni 110 {
+         vrf-target target:1:110;
+     }
+     vni 111 {
+         vrf-target target:1:111;
+     }
[edit policy-options policy-statement LEAF-IN]
     inactive: term default { ... }
+    term import_vni110 {
+        from community com110;
+        then accept;
+    }
+    term import_vni111 {
+        from community com111;
+        then accept;
+    }
[edit policy-options]
+   community com110 members target:1:110;
+   community com111 members target:1:111;
[edit routing-instances Type2]
+    interface irb.110;
+    interface irb.111;
[edit vlans]
+   v110 {
+       vlan-id 110;
+       l3-interface irb.110;
+       vxlan {
+           vni 110;
+       }
+   }
+   v111 {
+       vlan-id 111;
+       l3-interface irb.111;
+       vxlan {
+           vni 111;
+       }
+   }
changed: [qfx5110-4]

...
changed: [qfx5110-5]

...
changed: [qfx5110-6]

...
changed: [qfx5110-3]

TASK [add back default term in EVPN-host-routes policy] ************************

[edit policy-options policy-statement EVPN-host-routes]
     term from_MPLS_VPN { ... }
+    term default {
+        then reject;
+    }
changed: [qfx5110-6]

[edit policy-options policy-statement EVPN-host-routes]
     term from_lo0-1 { ... }
+    term default {
+        then reject;
+    }
changed: [qfx5110-5]

[edit policy-options policy-statement EVPN-host-routes]
     term from_static { ... }
+    term default {
+        then reject;
+    }
changed: [qfx5110-4]

[edit policy-options policy-statement EVPN-host-routes]
     term from_MPLS_VPN { ... }
+    term default {
+        then reject;
+    }
changed: [qfx5110-3]

PLAY RECAP *********************************************************************
qfx5110-3                  : ok=11   changed=3    unreachable=0    failed=0
qfx5110-4                  : ok=11   changed=3    unreachable=0    failed=0
qfx5110-5                  : ok=11   changed=3    unreachable=0    failed=0
qfx5110-6                  : ok=11   changed=3    unreachable=0    failed=0
```

Rolling back using Ansible if needed:

```
ansible-playbook pb.rollback.yml --diff -e "rb=3"                                                                           

PLAY [Rollback configuration on junos devices] *********************************

TASK [Rollback junos config task] **********************************************
changed: [qfx5110-3]
changed: [qfx5110-4]
changed: [qfx5110-6]
changed: [qfx5110-5]

PLAY RECAP *********************************************************************
qfx5110-3                  : ok=1    changed=1    unreachable=0    failed=0
qfx5110-4                  : ok=1    changed=1    unreachable=0    failed=0
qfx5110-5                  : ok=1    changed=1    unreachable=0    failed=0
qfx5110-6                  : ok=1    changed=1    unreachable=0    failed=0
```
