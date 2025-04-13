#!/bin/bash

echo "Analysis of the container events... (Logging Service fails -> Hazelcast Node fails, Logging Service restarts -> Hazelcast Node restarts)"
echo "------------------------------------"

docker events --filter 'event=die' --filter 'event=start' --format '{{.Actor.Attributes.name}}' | while read container_name
do
    if [[ "$container_name" == hm3-logging_service* ]]; then
        logging_service_container=$container_name
        
        hazelcast_node="${container_name/logging_service/hazelcast_node}"
        hazelcast_node="${hazelcast_node#hm3-}"        
        hazelcast_node="${hazelcast_node%-*}"

        if [[ $(docker ps -q -f name="$logging_service_container") != "" ]]; then
            echo "Container $logging_service_container restarted -> Restarting $hazelcast_node"
            echo "------------------------------------"
            docker start $hazelcast_node
        fi
        
        if [[ $(docker ps -q -f name="$logging_service_container") == "" ]]; then
            echo "Container $logging_service_container failed -> Stopping $hazelcast_node"
            echo "------------------------------------"
            docker stop $hazelcast_node
        fi

        
    fi
done
