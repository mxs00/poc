Creating mitm proxy as docker container

# mitm 

## setting local and remote ip-addresses
port 8086 is used as mitm proxy port. 
port 8081 is used as web browser port


command tag configuration for docker compsoe at the start of container is given below:

command: mitmweb --web-host 0.0.0.0 --no-web-open-browser -p 8086 --mode reverse:http://192.168.3.38:8083/


--mode reverse:http://x.x.x.x:port/ is used to configure endpoint that is being proxied by the mitm proxy, 