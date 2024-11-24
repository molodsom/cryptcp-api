#!/bin/bash

if [ ! -d /var/opt/cprocsp/keys/root ]; then
  echo "Creating the folder structure..."
  mkdir -p /var/opt/cprocsp/{dsrf/db{1,2},keys/root/hsm_keys,lmk,tmp,users/{root,stories}}
fi

gunicorn -b 0.0.0.0:80 app:app
