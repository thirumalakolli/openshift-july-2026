oc delete deploy/flask-app svc/flask-app route/flask-app bc/flask-app is/flask-app

oc delete -f mysql-svc.yml
oc delete -f mysql-deploy.yml
oc delete -f mysql-pvc.yml
oc delete -f mysql-pv.yml
oc delete -f mysql-secret.yml
