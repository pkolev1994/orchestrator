#!/usr/bin/perl

use strict;

my $tag;
my $clean_changelog;
my $latest_tag = `git for-each-ref --sort='-creatordate' | grep refs/tags/ | cut -d/ -f3 | head -n1 | tail -n1`;
my $previous_tag = `git for-each-ref --sort='-creatordate' | grep refs/tags/ | cut -d/ -f3 | head -n5 | tail -n1`;
chomp $previous_tag;
$previous_tag .= "..HEAD";
my $changelog = `git log $previous_tag --format='* %cd %cn <%ce> %n- (%h) %s%d%n' --date=local | sed -r 's/[0-9]+:[0-9]+:[0-9]+ //'`;
my $temp_changelog;
my $current_tag;
my $tags;
my $current_tag = $latest_tag;
chomp($current_tag);
while($changelog =~ /(\*\s*.*?\-.*?\n)/gs){
	$temp_changelog = $1;
	foreach(`git tag`){
		$tags = $_;
		chomp($tags);
		if($temp_changelog =~ /$tags/){
			$current_tag = $tags;
		}
	}
	if($1 =~ /Merge remote\-tracking/ or  $1 =~ /nochangelog|silentcommit/){
		next;
	} else {
		$temp_changelog =~ s/(<[^\@]+.[^\>]+>)/$1 $current_tag/gs;
		$clean_changelog .= $temp_changelog."\n";
	}
}

print $clean_changelog;
