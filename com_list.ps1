
$number = (Get-WMIObject Win32_PnPEntity | Where-Object {$_.name -match "com\d"}).Name
try{
	$name = (Get-WMIObject Win32_PnPEntity | Where-Object {$_.name -match "com\d"}).GetDeviceProperties("DEVPKEY_Device_BusReportedDeviceDesc").deviceProperties.Data
}catch{
	exit
}

$i=0
foreach($num in $number){
	$num = $num -replace "[^com\d\d]", ""
	if($exist -eq 1){
		break
	}else{
		[PSCustomObject]@{ Number = $num; Name = $name[$i] } | Export-Csv -NoTypeInformation -Path ./com_list.csv -Append
		$exist=1
	}
	$i++
	$exist=0
}