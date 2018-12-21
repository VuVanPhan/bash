#!/usr/bin/env bash
# filter ticket with query
source ./.env

#echo -n "Enter query filter the ticket for delete : "
#read query
#
#echo -n "Enter subdomain site you used : "
#read subdomain
#
#echo -n "Enter username admin : "
#read username
#
#echo -n "Enter password admin : "
#read -s password

# query example
#query="created=2018-12-11 type:ticket status:new IP: 45.117.239.146"
curl "https://$subdomain.zendesk.com/api/v2/search.json" -G --data-urlencode "query=$query" -v -u "$username":"$password" > test.txt

# get id ticket
data=$(cat test.txt)
da=''
# solution 1 : use for
array=(${data//,/ })
for i in "${!array[@]}"
do
    if [[ ${array[i]} != *'{"id":'* ]]; then
        if [[ ${array[i]} == *'"id":'* ]]; then
            temp=${array[i]}
            array2=(${temp//:/ })
            da+="${array2[1]},"
        fi
    fi
done
echo $da
arrayData=${da::${#da}-1}
echo "Delete ticket id : $arrayData"

## solution 2 : use while, but this's solution very dangerous because it can loop indefinitely
#while IFS=',' read -ra ADDR; do
#    for i in "${ADDR[@]}"; do
#        if [[ $i != *'{"id":'* ]]; then
#            if [[ $i == *'"id":'* ]]; then
#                IFS=':' read -r -a array <<< "$i"
#                da+="${array[1]},"
#            fi
#        fi
#    done
#done <<< $data

# delete file test.txt after filter
rm -f test.txt

# delete a tickets
#curl "https://$subdomain.zendesk.com/api/v2/tickets/$id.json" -v -u "$username":"$password" -X DELETE
# delete many tickets
curl "https://$subdomain.zendesk.com/api/v2/tickets/destroy_many.json?ids=$arrayData" -v -u "$username":"$password" -X DELETE