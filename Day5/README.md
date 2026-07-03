# Day 5

## Info - Openshift S2I
<pre>
- In Kubernetes, we can only deploy application using container images
- In Openshift, we can deploy applicaiton using container images and from github(or any other version control) url i.e from source code
- This feature in Openshift is called S2I ( Source to Image )
- Openshift supports many different types of strategies
  1. Docker 
  2. Source
  3. Custom
  4. Pipeline(Jenkins/TekTon)
  5. Binary(S2I Binary)
</pre>

## Lab - Deploying our custom spring-boot appliction into Openshift using S2I docker strategy
```
oc new-app --name=hello-microservice https://github.com/tektutor/openshift-july-2026.git --context-dir=Day5/simple-springboot-microservice --strategy=docker

oc expose svc/hello-microservice

oc logs -f bc/hello-microservice

oc get svc,route

curl --insecure http://hello-microservice-jegan.apps.ocp4.palmeto.org
```

## Lab - Horizontal Pod Auto-scaling based on CPU Utilization
```
oc delete project jegan
oc new-project jegan

cd ~
git clone https://github.com/tektutor/openshift-july-2026.git
cd openshift-june-2026
cd Day5/auto-scaling
oc create -f hello-deploy.yml --save-config=true
oc get pods
oc create -f hello-hpa.yml --save-config

oc expose deploy/nginx --port=8080
oc expose svc/nginx
oc get route
```

We need to stree the pod with more traffic
```
ab -k -n 200000 -c 1000 https://nginx-jegan.apps.ocp4.palmeto.org/
```
