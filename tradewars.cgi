#!/usr/bin/perl

use warnings;
use CGI;
use Data::Dumper;

my $q = CGI->new;

if($q->param('Action') eq 'reset'){
    $q->delete_all;
}
my @stuff = $q->param;

show_headers();

unless(($q->param('Action')eq 'calculate')||($q->param('Action') eq 'rerun')){
    show_form();
}else{
    show_attack();
}

show_footers();

exit();


sub show_headers {
    my @output = (
        $q->header('text/html'),
        $q->start_html('Planetary Defense Calculator'),
        $q->h1({-align=>CENTER},'TradeWars Web Utility'),
        $q->hr,
        $q->h2('Planetary Invasion Simulator'),);
    print join("\n",@output);
}

sub show_form {
    my @output = (
        $q->br,
        $q->start_form,
        "What Class of Planet:   ",
        $q->radio_group({-name=>'Planet_Type', -values=>['H','L','M'],-default=>'L'}),
        $q->br,
        "Amount of Fuel Ore on Planet: ",
        $q->textfield(-name=>'Fuel_Level',-value=>'48000'),
        $q->checkbox(-name=>'max fuel'),
        $q->br,
        "Citadel Level: ",
        $q->radio_group({-name=>'citadel', -values=>['2','3','4','5','6'],-default=>'5'}),
        $q->br,
        "Amount of Sector Fighters: ",
        $q->textfield(-name=>'Sector Fighters',-value=>'500'),
        $q->checkbox(-name=>'max fighters'),
        $q->br,
        "Amount of Planetary Shields: ",
        $q->textfield(-name=>'Planetary Shields',-value=>'40'),
        $q->br,
        "Amount of Planetary Fighters: ",
        $q->textfield(-name=>'Planetary Fighters',-value=>'13250'),
        $q->br,
        "Qcannon Sector Blast %: ",
        $q->textfield(-name=>'sector percentage',-value=>'4'),
        $q->br,
        "Qcannon Atmosphere Blast %: ",
        $q->textfield(-name=>'atmo percentage',-value=>'30'),
        $q->br,

        "What type of ship: ", 
        $q->radio_group({-name=>'ship', -values=>['Imperial Starship','Corporate Flagship','BattleShip'],-default=>'Imperial Starship'}),
        $q->br,
        $q->checkbox(-name=> 'Photon Missile'),
        $q->br,
        $q->submit('Action','calculate'),
        $q->submit('Action','reset'),
        $q->end_form,);
    print join("\n",@output);
}


sub show_attack {

    my %ship;
    my %planet;
    my %stats;
    my $ph = ($q->param('Photon Missile') eq 'on') ? 1: 0;
    if($q->param('ship')eq'Imperial Starship'){
        $ship{'fighters'}=50000;
        $ship{'odds'}=1.5;
        $ship{'shields'}=2000;
        $ship{'fpa'}=10000;
    } elsif ($q->param('ship') eq 'Corporate Flagship'){
        $ship{'fighters'}=20000;
        $ship{'odds'}=1.2;
        $ship{'shields'}=1500;
        $ship{'fpa'}=6000;
    } else {     # BattleShip
        $ship{'fighters'}=10000;
        $ship{'odds'}=1.6;
        $ship{'shields'}=750;
        $ship{'fpa'}=3000;
    }
    $ship{'d'} = $ship{'shields'} + $ship{'fighters'};

    my $ptype = $q->param('Planet_Type');

    if($q->param('max fuel')){
        if($ptype eq 'H'){
            $planet{'fuel'} = 1000000;
        }elsif ($ptype eq 'L'){
            $planet{'fuel'} = 200000;
        }else{
            $planet{'fuel'} = 100000;
        }
    } else {
        $planet{'fuel'} = $q->param('Fuel_Level');
    }
    if($q->param('max fighters')){
        $planet{'sector fighters'} = 1000000;
    }else{
        $planet{'sector fighters'} = $q->param('Sector Fighters');
    }
    
    $planet{'planetary shields'} = $q->param('Planetary Shields');
    $planet{'planetary fighters'} = $q->param('Planetary Fighters');
    $planet{'sector percent'} = $q->param('sector percentage');
    $planet{'atmo percent'} = $q->param('atmo percentage');
    $planet{'citadel'} = $q->param('citadel');

    my %planet_copy = %planet;
    my @o;
    
    push @o, "Attack Commencing...";
    while($planet{'planetary fighters'}>0){

        push @o , enter_sector(\%ship,\%planet);
        unless($ship{'fighters'}>0){
            last;
        }
        push @o, "Preparing to land on the planet...";
    
        push @o, land_on_planet(\%ship,\%planet);

        last;
    }
    my @op;
    push @op, $q->ul( map {$q->li({-type=>'disc'}, $_)}@o);
    push @op, after_action_report(\%ship,\%planet,\%planet_copy);

    print join("\n",@op);
}

sub enter_sector {
    my $ship = shift;
    my $planet = shift;
    my @o;
    push @o, "Entering the sector";
    my $ph = ($q->param('Photon Missile') eq 'on') ? 1: 0;
    my $sq = (($planet->{'citadel'}>2)&&($planet->{'sector percent'}>0)&&($planet->{'fuel'}>0)) ? 1 : 0;
    if((not $ph && ($planet->{'sector fighters'}||$sq))||($sq && $planet->{'planetary shields'} >=200)){
        do {
            push @o, sector_quasar_shot($ship,$planet);
            push @o, attack_sector_fighters($ship, $planet);
        } while (($planet->{'sector fighters'}>0)&&(not $ph));
    }

    return @o;
}

sub sector_quasar_shot {
    my $ship = shift;
    my $planet = shift;
    my @o;
    my $sq = (($planet->{'citadel'}>2)&&($planet->{'sector percent'}>0)&&($planet->{'fuel'}>0)) ? 1 : 0;
    if($sq){
        my $sp = $planet->{'sector percent'} / 100;
        my $fu = int($planet->{'fuel'}* $sp);
        $planet->{'fuel'} -= $fu;
        my $shot = int($fu/3);
        if($shot > $ship->{'d'}){
            $ship->{'shields'}=$ship->{'fighters'}=0;
            push @o, "Qcannon blast of ".$shot." has destroyed the attacker.";
            return @o;
        }
        push @o, qcannon_hit($ship,$planet,$shot);
    }
    return @o;
}

sub attack_sector_fighters {
    my $ship = shift;
    my $planet = shift;
    my $ph = ($q->param('Photon Missile') eq 'on') ? 1: 0;
    my $sf = $planet->{'sector fighters'};
    if($sf>0 && not $ph){
        my $a;
        if($sf>int($ship->{'odds'} * $ship->{'fpa'})){
            $a = ($ship->{'fighters'} >= $ship->{'fpa'}) ? $ship->{'fpa'} : $ship->{'fighters'};
            my $sfl = int($ship->{'odds'} * $a);
            $planet->{'sector fighters'} -= $sfl;
            $ship->{'fighters'} -= $a;
            $ship->{'d'} = $ship->{'shields'}+$ship->{'fighters'};
            push @o, "Attacker destroys ".$sfl." sector fighters, ".$planet->{'sector fighters'}." remain. Attacker has ".$ship->{'fighters'}." remaining.";
        }else{
            $a = int($sf/$ship->{'odds'});
            $ship->{'fighters'} -= $a;
            $planet->{'sector fighters'} = 0;
            $ship->{'d'} = $ship->{'fighters'} + $ship->{'shields'};
            push @o, "Attacker destroys all ".$sf." sector fighters. Attacker has ".$ship->{'fighters'}." remaining.";
        }
    }
    return @o;
}

sub land_on_planet {
    my $ship = shift;
    my $planet = shift;
    my @o;
    my $ph = ($q->param('Photon Missile') eq 'on') ? 1: 0;
    $ship->{'d'} = $ship->{'shields'}+$ship->{'fighters'};
    push @o, "Attacker encounters planetary shields" if $planet->{'planetary shields'};
    my $aq = (($planet->{'citadel'}>2)&&($planet->{'atmo percent'}>0)&&($planet->{'fuel'}>0)) ? 1 : 0;
    do {
        $aq = (($planet->{'citadel'}>2)&&($planet->{'atmo percent'}>0)&&($planet->{'fuel'}>0)) ? 1 : 0;
        if($aq && (($ph!=1) || ($planet->{'planetary shields'}>=200))){
            my $shot = int($planet->{'fuel'} * ($planet->{'atmo percent'}/100));
            $planet->{'fuel'} -= int($shot/2);
            if($ship->{'d'} < $shot){
                ship_destroyed($ship);
                push @o, "Atmospheric Qcannon did ".$shot." damage, destroying the attacker.";
                return @o;
            }else{
                push @o, qcannon_hit($ship,$planet,$shot);
            }
        }
        
        if($ship->{'fighters'}==0){
            return @o;
        }
        if($planet->{'planetary shields'}>0){
            my $f = int($ship->{'fpa'} * $ship->{'odds'});
            my $fa = int($f/20);
            my $full = ($ship->{'fighters'} > $ship->{'fpa'}) ? 1 : 0;
            if($full){
                push @o, attack_planetary_shields($ship,$planet,$fa);
            } else {
                $f = int($ship->{'fighters'} * $ship->{'odds'});
                $fa = int($f/20);
                push @o, attack_planetary_shields($ship,$planet,$fa);
            }
            if($planet->{'planetary fighters'}==0){
                return @o;
            }
        } else{
            my $f = int($ship->{'fpa'} * $ship->{'odds'});
            my $fa = int($f/3);
            my $full = ($ship->{'fighters'} > $ship->{'fpa'}) ? 1 : 0;
            if($full){
                push @o, attack_planetary_fighters($ship,$planet,$fa);
            } else {
                $f = int($ship->{'fighters'} * $ship->{'odds'});
                $fa = int($f/3);
                push @o, attack_planetary_fighters($ship,$planet,$fa);
            }
            if($planet->{'planetary fighters'}==0){
                return @o;
            }
        }
        
    } while ($planet->{'planetary fighters'}>0);
    return @o;
}

sub attack_planetary_fighters {
    my $ship = shift;
    my $planet = shift;
    my $fa = shift;
    my @o;
    if($fa >= $planet->{'planetary fighters'}){
        my $tf = int((3 * $planet->{'planetary fighters'})/$ship->{'odds'});
        $ship->{'fighters'} -= $tf;
        $planet->{'planetary fighters'} = 0;
        return take_planet($ship->{'fighters'});
    }
    $planet->{'planetary fighters'} -= $fa;
    if($ship->{'fighters'}>=$ship->{'fpa'}){
        $ship->{'fighters'}-=$ship->{'fpa'};
    } else {
        $ship->{'fighters'}=0;
    }
    return "Attacker destroyed ".$fa." planetary fighters, ".$planet->{'planetary fighters'}." remain. The attacker has ".$ship->{'fighters'}." fighters remaining.";
}

sub attack_planetary_shields {
    my $ship = shift;
    my $planet = shift;
    my $fa = shift;
    my @o;
    if($fa >= $planet->{'planetary shields'}){
        my $tf = int((20 * $planet->{'planetary shields'})/$ship->{'odds'});
        $ship->{'fighters'} -= $tf;
        $planet->{'planetary shields'} = 0;
        return shields_destroyed($ship->{'fighters'});
    }
    $planet->{'planetary shields'} -= $fa;
    if($ship->{'fighters'}>= $ship->{'fpa'}){
        $ship->{'fighters'}-=$ship->{'fpa'};
    } else {
        $ship->{'fighters'}=0;
    }
    return "Attacker destroyed ".$fa." planetary shields, ".$planet->{'planetary shields'}." remain. The attacker has ".$ship->{'fighters'}." fighters remaining.";
}

sub shields_destroyed {
    my $fighters = shift;
    my @o;
    push @o, "Attacker has destroyed all planetary shields, proceeding with the invasion. Attacker has ".$fighters." fighters remaining.";
    return @o;
}

sub take_planet {
    my $fighters = shift;
    my @o;
    push @o, ("Attacker has destroyed the remaining planetary fighters. ".$fighters." fighters remain on the attacker's ship.", "The attacker has taken the planet.");
    return @o;
}

sub qcannon_hit {
    my $ship = shift;
    my $planet = shift;
    my $shot = shift;
    if($shot <= $ship->{'shields'}){
        $ship->{'shields'}-= $shot;
    } else {
        $ship->{'fighters'}-= $shot - $ship->{'shields'};
        $ship->{'shields'}=0;
    }
    if($ship->{'fighters'}<0){
        ship_destroyed($ship);
        return "Qcannon blast of ".$shot." has destroyed the attacker.";
    }
    $ship->{'d'} = $ship->{'fighters'}+$ship->{'shields'};
    return "Qcannon blast of ".$shot." hits the attacker. ".$ship->{'d'}." defensive points remaining.";
}

sub ship_destroyed {
    my $ship = shift;
    $ship->{'d'} = 0;
    $ship->{'shields'} = 0;
    $ship->{'fighters'} = 0;
}

sub after_action_report {
    my $ship = shift;
    my $planet = shift;
    my $planet_copy = shift;
    my @o;
    
    push @o, ($q->hr,$q->h3("After Action Report"));
    if($ship->{'fighters'}==0){
        push @o, ("The attacker was unsuccessful.", $q->br);
        push @o, ($planet->{'sector fighters'}." sector fighters remain.",
                    $planet->{'planetary shields'}." planetary shields remain.",
                    $planet->{'planetary fighters'}." planetary fighters remain.",$q->br);
    } else {  
        push @o, ("The attacker has taken the planet.", $q->br);
        push @o, ("The attacker has ".$ship->{'fighters'}." fighters remaining.", $q->br);
    }
    push @o, ("The planet went from ".$planet_copy->{'fuel'}." fuel to ".$planet->{'fuel'}." after the attack.",$q->br);

    push @o, ($q->start_form, $q->br, $q->submit('Action','reset'));

    return @o;
}

sub show_footers {
    my @output = (
        $q->br,
        $q->end_html,);
    print join("\n",@output);
}

