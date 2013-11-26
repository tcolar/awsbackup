''' 
 AWS Backup script
 Thibaut Colar - 5/21/13
 
Requires boto (tested with 2.9)
'''
from datetime import datetime, timedelta
import boto
import boto.ec2
import boto.utils
import json
import sys
import time
import tarfile

def conn_to_region(region):
	return boto.ec2.connect_to_region(
		region, 
		aws_access_key_id = key, 
		aws_secret_access_key = secret)

def backup_ec2_instance(ec2):	
	print(datetime.now())
	region = ec2["region"]
	keep = ec2["keep"]
	print("[EC2 Backing up instance {0} ({1}) {2}]".format(ec2["name"], ec2["instance"], region))
	conn = conn_to_region(region)
	volumes = conn.get_all_volumes(filters={'attachment.instance-id': ec2["instance"]}) 
	new_snaps = []
	
	# Snapshot volumes locally
	for volume in volumes:
		snap = backup_ec2_volume(ec2, conn, volume)
		new_snaps.append(snap)
	
	# Trim local snapshots
	for volume in volumes:
		trim_snapshots(ec2, conn, volume.id, region, keep)
	
	# Copy new snapshots to another region
	if "copy_to" in ec2:
		copy_days = [0,1,2,3,4,5,6,7]
		if "copy_days" in ec2:
			copy_days = ec2["copy_days"]
			
		to_region = ec2["copy_to"]
		to_conn = conn_to_region(to_region)	
		
		if not day in copy_days:
			print "\t- No snapshot copy for {0} today.".format(ec2["name"])
		else:			
			for snap in new_snaps:			
				copy_ec2_snapshot(to_conn, to_region, region, snap)

		# Trim snapshots in that region
		for volume in volumes:
			trim_snapshots(ec2, to_conn, volume.id, to_region, ec2["copy_keep"])

def backup_ec2_volume(ec2, conn, volume):
	desc = "{0} | {1} | {2}".format(ec2["name"], ec2["instance"], volume.id)
	print("\t- Snapshoting {0} ({1} - {2} GB)".format(desc, volume.tags["Name"], volume.size))
	snap = volume.create_snapshot(desc)
	# We wait for the copy to complete so won't get error when trying to copy it
	while conn.get_all_snapshots(snap.id)[0].status != "completed":
		time.sleep(3)
	conn.create_tags(snap.id, {"SrcVol" : volume.id})
	print("\t- Snapshot done with ID: {0}".format(snap.id))
	return snap

def copy_ec2_snapshot(conn, to_region, region, snap):
	print("\t- Copying {0}({1}) {4} from {2} to {3}".format(snap.id, snap.description, region, to_region, snap.tags["Name"]))
	new_id = conn.copy_snapshot(region, snap.id, snap.description)
	conn.create_tags(new_id, {"Name": snap.tags["Name"], "SrcVol" : snap.volume_id})
	
	# We wait for the copy to complete (Note: Amazon allows up to 5 concurrent max)
	while conn.get_all_snapshots(new_id)[0].status != "completed":
		time.sleep(30)
	print "\t- Snapshot copy completed with id {0} at {1}".format(new_id, datetime.now()) 	

def trim_snapshots(ec2, conn, volume_id, region, keep):
	# find snapshots own by us for a given volume in the curent connection(& region)
	all_snaps = conn.get_all_snapshots(owner = 'self')
	snapshots = []
	for snap in all_snaps:
		# We use a custom tag because snap.volume_id does not stay consistent when copied to another region
		if "SrcVol" in snap.tags and snap.tags["SrcVol"] == volume_id:
			snapshots.append(snap)
		
	snapshots.sort(snap_compare)
	cpt = 0
	for snapshot in snapshots:
		cpt += 1
		if(cpt > keep):
			print "\t - Deleting {3}({0}) : {1} ({2})".format(region, snapshot.description, snapshot.start_time, snapshot.id)
			snapshot.delete()
		#else:
		#	print "\t - Keeping {3}({0}) : {1} ({2})".format(region, snapshot.description, snapshot.start_time, snapshot.id)


def snap_compare(snap1, snap2):
	''' compare method to sort snapshots by date, newer first'''
	if snap1.start_time < snap2.start_time:
		return 1
	elif snap1.start_time == snap2.start_time:
		return 0
	return -1

def dump_db(): # TODO, make db dump and save in s3 ?
	''' Dump a RDS(MySql) database'''
	pass
    
##################################################################  Main 

json_data=open('aws.json')
data = json.load(json_data)
day = now = datetime.today().weekday() # Monday is zero

key = data["access_key"]
secret = data["secret_key"]

print "Today's weekday is {0}".format(day)

#EC2 snapshots
ec2s = data["ec2_snapshots"]
for ec2 in ec2s:
	backup_ec2_instance(ec2)	

print "Completed at {0}".format(datetime.now())
