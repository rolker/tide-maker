import json
import boto3
import os
import re
import subprocess

"""
Python TippeCanoe binary wrapper.
@author github:@StreamlinesUNH
Modified into a cloud-native SQL Egress via Lambda to AWS DynamoDB
"""

from mbutil import mbtiles_to_disk

s3_client = boto3.client("s3")


def gen_mbtiles(infile):
    env = os.environ.copy()

    env["LD_LIBRARY_PATH"] = "/opt/lib"
    process = subprocess.Popen(["/opt/tippecanoe",
                                "-o", "/tmp/" + infile + ".mbtiles", "/tmp/" + infile + ".geojson",
                                "--maximum-zoom=14"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               env=env
                               )

    return process


def lambda_handler(event, context):
    """
    S3 File I/O Here
    REAL I/O
    """
    infile = event["Records"][0]["s3"]["object"]["key"]
    s3_obj = s3_client.get_object(
        Bucket=event["Records"][0]["s3"]["bucket"]["name"],
        Key=infile
    )

    data_location = infile.split("/")[0] + "-" + str(int(re.findall(r'\d+', infile)[0]))
    infile = (infile.replace("/", "")).split(".")[0]

    print("Infile is " + data_location)

    geoJson = s3_obj["Body"].read()
    localCache = open("/tmp/" + infile + ".geojson", "wb")
    localCache.write(geoJson)
    localCache.close()

    '''
    Generate MBTile & store it at: /tmp/tmp.mbtiles
    '''
    process = gen_mbtiles(infile)
    process.wait()

    print("MBTILE Generated")

    """
    Slice MBTile here
    """
    mbtiles_to_disk("/tmp/" + infile + ".mbtiles", data_location)

    return {
        'statusCode': 200,
        'body': json.dumps('Processed GeoJSON to MVT and pushed to Lambda')
    }
