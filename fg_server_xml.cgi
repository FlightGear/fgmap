#!/usr/bin/perl -wT

use strict;
use IO::Socket;
use Math::Trig;

#$server = "81.169.158.37";
my($server) = "localhost";
my($port) = 5003;

my($xml) = "";
my($l);

my($kml_mode) = 0;



if(!defined($ENV{'QUERY_STRING'}))
{
    exit(-1);
}

($server, $port) = ($ENV{'QUERY_STRING'} =~ m#(.*?):(\d+)#);

if(!defined($server) || !(defined($port)))
{
    exit(-1);
}

$server =~ s#></\\&\?\|\!\*##g;
$port =~ s#></\\&\?\|\!\*##g;

my($pilot_total) = 0;
my($pilot_cnt) = 0;

my($socket) = IO::Socket::INET->new(PeerAddr => $server,
                                    PeerPort => $port,
                                    Proto => "tcp",
                                    Type => SOCK_STREAM,
                                    Timeout => 10);
if($socket)
{
    while($l = <$socket>)
    {
        my($callsign, $server_ip, $lng, $lat, $alt, $model);

        chomp($l);

        if(substr($l, 0, 1) eq "#")
        {
            if($l =~ /^# (\d+) .*? online/)
            {
                $pilot_total = $1;
            }
            next;
        }

        ($callsign, $server_ip, $lat, $lng, $alt, $model) =
            ($l =~ m/(.*?)@(.*?): .*? .*? .*? (.*?) (.*?) (.*?) (.*?)$/);

        # Aircraft/ComperSwift/Models/ComperSwift-model.x

        if($callsign and $model)
        {
            #$model =~ s#.*/(.*?)\..*?$#$1#;
            $model =~ s#.*/(.*?)#$1#;
            $model =~ s#\..*?$##;

            $xml .= "\t<marker server_ip=\"${server_ip}\" callsign=\"${callsign}\" lng=\"${lng}\" lat=\"${lat}\" alt=\"${alt}\" model=\"${model}\" />\n";

            $pilot_cnt++;

            if($pilot_cnt >= $pilot_total)
            {
                close($socket);
                undef($socket);
                last;
            }
        }
    }

    if($socket)
    {
        close($socket);
    }
}

my($testing) = 0;

if($testing)
{
    $xml .= "\t<marker server_ip=\"server\" callsign=\"testing\" lng=\"-122.357237\" lat=\"37.613545\" alt=\"100\" model=\"model\" />\n";
}

print("Pragma: no-cache\r\n");
print("Cache-Control: no-cache\r\n");
print("Expires: Sat, 17 Sep 1977 00:00:00 GMT\r\n");
print("Content-Type: text/xml\r\n\r\n");

print("<fg_server pilot_cnt=\"$pilot_cnt\">\n");
print($xml);
print("</fg_server>\n\n");

exit(0);





## A few simgear functions implemented in/converted into Perl
## And don't ask!

my($PI) = 3.14159265358979323846;
my($DEG_TO_RAD) = $PI/180.0;
my($SGLIMITS_MIN) = 1.17549e-38; # SGLimits<T>::min()


# SGQuat::fromAngleAxis(const SGVec3<T>& axis)
sub from_angle_axis
{
    my($x, $y, $z) = @_;
    my($q1, $q2, $q3, $q4);

    my($nAxis) = sqrt($x * $x + $y * $y + $z * $z);	# norm

    if($nAxis <= $SGLIMITS_MIN)
    {
	$q1 = 1;
	$q2 = 0;
	$q3 = 0;
	$q4 = 0;
    }
    else
    {
	my($angle2) = 0.5 * $nAxis;
	my($b) = sin($angle2)/$nAxis;

	# SGQuatf::fromRealImag
	$q1 = cos($angle2);
	$q2 = $x * $b;
	$q3 = $y * $b;
	$q4 = $z * $b;
    }

    return ($q1, $q2, $q3, $q4);
}


# SGQuat::fromLonLatRad(T lon, T lat)
sub from_lon_lat_rad
{
    my($lon_rad, $lat_rad) = @_;
    my($w, $x, $y, $z);
    my($zd2) = 0.5 * $lon_rad;
    my($yd2) = -0.25 * $PI - 0.5 * $lat_rad;
    my($Szd2) = sin($zd2);
    my($Syd2) = sin($yd2);
    my($Czd2) = cos($zd2);
    my($Cyd2) = cos($yd2);
    $w = $Czd2 * $Cyd2;
    $x = -$Szd2 * $Syd2;
    $y = $Czd2 * $Syd2;
    $z = $Szd2 * $Cyd2;
    return ($w, $x, $y, $z);
}


sub get_euler_deg
{
    my($w, $x, $y, $z) = @_;
    my($xRad, $yRad, $zRad);

    # getEulerRad

    my($sqrQW) = $w * $w;
    my($sqrQX) = $x * $x;
    my($sqrQY) = $y * $y;
    my($sqrQZ) = $z * $z;

    my($num) = 2 * ($y * $z + $w * $x);
    my($den) = $sqrQW - $sqrQX - $sqrQY + $sqrQZ;

    if (abs($den) < $SGLIMITS_MIN && abs($num) < $SGLIMITS_MIN)
    {
	$xRad = 0;
    }
    else
    {
	$xRad = atan2($num, $den);
    }
    
    my($tmp) = 2 * ($x * $z - $w * $y);

    if($tmp < -1)
    {
	$yRad = 0.5 * $PI;
    }
    elsif(1 < $tmp)
    {
	$yRad = -0.5 * $PI;
    }
    else
    {
	$yRad = -asin($tmp);
    }
   
    $num = 2 * ($x * $y + $w * $z); 
    $den = $sqrQW + $sqrQX - $sqrQY - $sqrQZ;
    if(abs($den) < $SGLIMITS_MIN && abs($num) < $SGLIMITS_MIN)
    {
	$zRad = 0;
    }
    else
    {
	my($psi) = atan2($num, $den);
	if($psi < 0)
	{
	    $psi += 2 * $PI;
	}
	$zRad = $psi;
    }
    
    return ($zRad * 180 / $PI, $yRad * 180 / $PI, $xRad * 180 / $PI);
}


# Returns (head, pitch, roll)
sub euler_get
{
    my($lat, $lon, $ox, $oy, $oz) = @_;
    my($heading, $pitch, $roll);

    # SGQuatf ecOrient = SGQuatf::fromAngleAxis(angleAxis);
    my(@ecOrient) = from_angle_axis($ox, $oy, $oz);

    my($lat_rad) = $lat * $DEG_TO_RAD;
    my($lon_rad) = $lon * $DEG_TO_RAD;

    # SGQuatf qEc2Hl = SGQuatf::fromLonLatRad(lon_rad, lat_rad);
    my(@qEc2Hl) = from_lon_lat_rad($lon_rad, $lat_rad);
#    print("$qEc2Hl[0] $qEc2Hl[1] $qEc2Hl[2] $qEc2Hl[3]\n");

    # SGQuatf hlOr = conj(qEc2Hl) * ecOrient;
    my(@conj) = ($qEc2Hl[0], -$qEc2Hl[1], -$qEc2Hl[2], -$qEc2Hl[3]);
#    print("$conj[0] $conj[1] $conj[2] $conj[3]\n");

    # SGQuatf hlOr = conj(qEc2Hl) * ecOrient
    my(@hlOr);
    $hlOr[1] = $conj[0] * $ecOrient[1] + $conj[1] * $ecOrient[0] + $conj[2] * $ecOrient[3] - $conj[3] * $ecOrient[2];
    $hlOr[2] = $conj[0] * $ecOrient[2] - $conj[1] * $ecOrient[3] + $conj[2] * $ecOrient[0] + $conj[3] * $ecOrient[1];
    $hlOr[3] = $conj[0] * $ecOrient[3] + $conj[1] * $ecOrient[2] - $conj[2] * $ecOrient[1] + $conj[3] * $ecOrient[0];
    $hlOr[0] = $conj[0] * $ecOrient[0] - $conj[1] * $ecOrient[1] - $conj[2] * $ecOrient[2] - $conj[3] * $ecOrient[3];
#    print("$hlOr[0] $hlOr[1] $hlOr[2] $hlOr[3]\n");

    # hlOr.getEulerDeg(hDeg, pDeg, rDeg);
    return get_euler_deg(@hlOr);
}




