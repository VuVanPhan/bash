#!/bin/bash
echo -n "Enter number character pass : "
read number

if [ $number -lt 7 ] || [ $number -gt 24 ]; then
   echo "Pass should be greater than 7 and less than 24 character"
   exit;
fi

# use dev/urandom
#</dev/urandom tr -dc 'A-Za-z0-9!"#$%&'\''()*+,-./:;<=>?@[\]^_`{|}~' | head -c $number  ; echo
#</dev/urandom tr -dc 'A-Za-z0-9!"#$%&'\''()*+,-./:;<=>?@[\]^_`{|}~' |  fold -w $number | head -n 1 ; echo

# use code generate
chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!"#$%&'\''()*+,-./:;<=>?@[\]^_`{|}~'
for (( i = 0; i < $number; i++ )); do
    echo -n "${chars:RANDOM%${#chars}:1}"
done
echo
