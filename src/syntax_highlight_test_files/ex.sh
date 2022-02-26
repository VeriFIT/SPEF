#!/bin/bash
E_PARAM_ERR=-198    # If less than 2 params passed to function.
EQUAL=-199          # Return value if both params equal.

max2 ()             # Returns larger of two numbers.
{                   # Note: numbers compared must be less than 257.
if [ -z "$2" ]
then
  return $E_PARAM_ERR
fi

if [ "$1" -eq "$2" ]
then
  return $EQUAL
else
  if [ "$1" -gt "$2" ]
  then
    return $1
  else
    return $2
  fi
fi
}

function greeting() {
    dereference ()
    {
        y=\$"$1"   # Name of variable.
        echo $y    # $Junk

        x=`eval "expr \"$y\" "`
        echo $1=$x
        eval "$1=\"Some Different Text \""  # Assign new value.
    }

    Junk="Some Text"
    echo $Junk "before"    # Some Text before
    dereference Junk
    echo $Junk "after"     # Some Different Text after
}

Year=`date +%Y`
Month=`date +%m`
Day=`date +%d`
echo `date`
echo "Current Date is: $Day-$Month-$Year"
