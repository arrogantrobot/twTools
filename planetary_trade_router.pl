#!/usr/bin/perl

#   This is a utility for creating routes along which to move planets in 
#   the BBS door game TradeWars 2002, so that one might sell organics and 
#   make tonnes of money. The required params to run are:
#   --warps  <path to my CIM sector report>
#   --ports <path to my CIM port report>
#   --start <sector number> 
#
#   see the GetOptions call below for more params


use strict;
use warnings;
use IO::File;
use Data::Dumper;
use Getopt::Long;
use Term::ANSIColor;

my $min_org = -1000;
my $min_org_percentage = 0.8;

my %sectors;
my $start = 1835;
my $stop = -1;
my $max_fuel='';
my $max_holds='';
my $warps_file='';
my $ports_file='';
my $max_ports='';


GetOptions( 'min_org' => \$min_org,
        'min_org_percentage' => \$min_org_percentage,
        'start=i' => \$start,
        'stop' => \$stop,
        'max-fuel=s' => \$max_fuel,
        'max-holds=s' => \$max_holds,
        'max-ports=s' => \$max_ports,
        'warps=s' => \$warps_file,
        'ports=s' => \$ports_file,
);

if($stop == -1){
    $stop = $start;
}

my $current_sector = $start;

init();

my $total_distance;
my $total_organics;
my $final_leap;

for (1..100){
    my $next_port  = find_nearest_o($current_sector);
    my $distance  = find_distance($current_sector,$next_port);
    $total_distance+= $distance;
    $total_organics+= $sectors{$next_port}{port}{o}*(-1);
    print "Move \t"; print color 'red'; print $distance; print color 'reset'; print "\t warps to sector \t";
    print color 'cyan'; print $next_port; print color 'reset'; print "\t which is selling ";
    print color 'green'; print $sectors{$next_port}{port}{o}; print color 'reset'; print " organics.\n";
    delete $sectors{$next_port}{port};
    $current_sector = $next_port;
    $final_leap = find_distance($current_sector,$start);
    if(defined($max_fuel)){
        if((($final_leap+$total_distance)*400) >= $max_fuel){
            print color 'red';
            print "\nReached max fuel, returning home.\n";
            print color 'reset';
            last;
        }
    }
    if($max_holds){
        if($total_organics >= $max_holds){
            print color 'red';
            print "\nReached max holds, returning home.\n";
            print color 'reset';
            last;
        }
    }
    if($max_ports){
        if($_ >= $max_ports){
            print color 'red';
            print "\nReached max ports, returning home.\n";
            print color 'reset';
            last;
        }
    }
}

$total_distance+=$final_leap;

print "\nAnd the final leap, the leap home: "; print color 'red'; print $final_leap; print color 'reset'; print " warps.\n";
print "\nA total distance of "; print color 'red'; print $total_distance; print color 'reset'; print " using "; print color 'red';
print ($total_distance*400); print color 'reset'; print " holds of fuel ore.\n";
print "Moving "; print color 'green'; print $total_organics; print color 'reset'; print " holds of organics.\n\n";


sub find_nearest_o {
    my $sector = shift;
    my $orig_sector = $sector;
    my %explored;
    $explored{$sector} = 1;
    my $found = 0;
    my @warps = @{ $sectors{$sector}{warps} };
    my @next_warps;
    while(@warps){
        while(@warps){
            $sector = shift @warps;
            $explored{$sector} = 1;
            if(exists($sectors{$sector}{port}) && 
                    ($sectors{$sector}{port}{o} <= $min_org) &&
                    ($sectors{$sector}{port}{op} >= $min_org_percentage)){
                return $sector;	
            } else {
                my @thing = @{ $sectors{$sector}{warps} };
                push @next_warps, grep { not exists($explored{$_}) }  @thing;
            }
        }
        push @warps, @next_warps;
    }
    die "Found no organics purchasing ports adjacent to ".$orig_sector;
}

sub find_distance {
    my $from = shift;
    my $to = shift;
    my %explored;
    my $found = 0;
    my @warps = @{ $sectors{$from}{warps} };
    my @next_warps;
    my $distance = 1;
    while(@warps){
        while(@warps){
            my $sector = shift @warps;
            if($sector == $to) {
                return $distance;
            }

            $explored{$sector} = $distance;
            push @next_warps, grep { not exists($explored{$_}) }  @{ $sectors{$sector}{warps} };
        }
        $distance++;
        push @warps, @next_warps;
    }
    die "Found no path from ".$from." to ".$to."\n";
}

sub init {
    unless(-s $warps_file){
        die "Could not locate warps_file at: ".$warps_file;
    }
    unless(-s $ports_file){
        die "Could not locate ports_file at: ".$ports_file;
    }

    my $sector_fh = IO::File->new($warps_file, "r");
    my $port_fh = IO::File->new($ports_file, "r");

    $sector_fh->getline; #toss throwaway line
        $port_fh->getline; #toss throwaway line

        while(my $line = $sector_fh->getline){
            chomp $line;
            my (undef, $sector, @warps) = split /\s+/, $line;
            unless(defined($sector) && ($sector =~ m/[0-9]/)){
                next;
            }
            my %sector;
            $sector{warps} = \@warps;
            $sectors{$sector} = \%sector;
        }
    $sector_fh->close;

    while(my $line = $port_fh->getline){
        chomp $line;
        my (@port) = split /\s+/, $line;
        my $sector = $port[1];
        map { shift @port } (1..2);
        unless(defined($sector) && ($sector =~ m/[0-9]/)){
            next;
        }
        port_fill(\@port, $sector);
    }
    $port_fh->close;
}

sub port_fill {
    my $port = shift;
    my $sector = shift;
    my @port = @{$port};
    @port = grep{ defined($_) } @port;

    #FUEL ORE
    my $r = shift @port;
    my $f;
    if ($r eq "-"){
        $f = (shift @port) * -1;
    } else { 
        $f = $r;
    }
    $sectors{$sector}{port}{f} = $f;
    $r = shift @port;
    while(! $r){
        $r = shift @port;
    }
    $r =~ s/\%//;
    $sectors{$sector}{port}{fp} = $r/100;

    #ORGANICS
    $r = shift @port;
    my $o;
    if ($r eq "-"){
        $o = (shift @port) * -1;
    } else { 
        $o = $r;
    }
    $sectors{$sector}{port}{o} = $o;
    $r = shift @port;
    while(! $r){
        $r = shift @port;
    }
    $r =~ s/\%//;
    $sectors{$sector}{port}{op} = $r/100;

    #EQUIPMENT
    $r = shift @port;
    my $e;
    if ($r eq "-"){
        $e = (shift @port) * -1;
    } else { 
        $e = $r;
    }
    $sectors{$sector}{port}{e} = $e;
    $r = shift @port;
    while(! $r){
        $r = shift @port;
    }
    $r =~ s/\%//;
    $sectors{$sector}{port}{ep} = $r/100;


#print join("_|_",@{$port})."\n";
#print Dumper($sectors{$sector}{port});
}
