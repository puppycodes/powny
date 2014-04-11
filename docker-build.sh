#!/bin/bash -x

dir="$1"
from="$2"

if [ -z "$dir" -o -z "$from" ]; then
	echo "usage: $0 <DIR> <FROM> <docker-build opts...>"
	exit 1
fi

shift
shift

orig="$dir/Dockerfile"
backup="$dir/.Dockerfile.bak"

cp "$orig" "$backup"
sed -i -e "s|^FROM .*$|FROM $from|g" "$orig"
docker build $@ "$dir"
retval=$?
mv "$backup" "$orig"
exit $retval
