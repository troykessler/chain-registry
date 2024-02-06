import os
import json
import requests
import time
import csv
from dateutil import parser

dir_path = "."
dirs = os.listdir(dir_path)

chains = []


print("gathering cosmos chains...")

for file_path in dirs:
  if not file_path.startswith("_") and not file_path.startswith(".") and not file_path == "testnets":
    if os.path.isdir(os.path.join(dir_path, file_path)):
      chains.append(file_path)

chains = sorted(chains)
print("found {} mainnet chains".format(len(chains)))

body = """
query ZonesTable {
  flat_blockchains(where: {is_mainnet: {_eq: true}}) {
    network_id
    blockchain_switched_stats(where: {is_mainnet: {_eq: true}, timeframe: {_eq: 720}}) {
      ibc_transfers
      ibc_cashflow
    }
    blockchain_stats(where: {timeframe: {_eq: 720}}) {
      txs
      active_addresses_cnt
    }
  }
}
"""

response = requests.post(url="https://api2.mapofzones.com/v1/graphql", json={"query": body})
ibc_chains = response.json()['data']['flat_blockchains']

print("found {} ibc chains".format(len(ibc_chains)))

with open("chains.csv", 'a', newline='') as csvfile:
  writer = csv.writer(csvfile)
  writer.writerow([
    'name',
    'website',
    'chain_id',
    'seeds',
    'persistent_peers',
    'rpcs',
    'apis',
    'block_height',
    'block_speed',
    'usd_price',
    'usd_market_cap',
    'usd_fully_diluted_valuation',
    'usd_24h_volume',
    'ibc_30d_volume',
    'ibc_30d_transfers',
    '30d_txs',
    '30d_active_addresses'
  ])

  for i in range(len(chains)):
    if os.path.exists(os.path.join(dir_path, chains[i], "chain.json")) and os.path.exists(os.path.join(dir_path, chains[i], "assetlist.json")):
      info = {
        'name': '',
        'website': '',
        'chain_id': '',
        'seeds': 0,
        'persistent_peers': 0,
        'rpcs': 0,
        'apis': 0,
        'block_height': 0,
        'block_speed': 0,
        'usd_price': 0,
        'usd_market_cap': 0,
        'usd_fully_diluted_valuation': 0,
        'usd_24h_volume': 0,
        'ibc_30d_volume': 0,
        'ibc_30d_transfers': 0,
        '30d_txs': 0,
        '30d_active_addresses': 0
      }

      f_chain = open(os.path.join(dir_path, chains[i], "chain.json"))
      f_assetlist = open(os.path.join(dir_path, chains[i], "assetlist.json"))
      chain = json.load(f_chain)
      assetlist = json.load(f_assetlist)
      f_chain.close()
      f_assetlist.close()

      info['name'] = chain['pretty_name']
      info['chain_id'] = chain['chain_id']

      if 'website' in chain:
        info['website'] = chain['website']

      if 'peers' in chain:
        if 'seeds' in chain['peers']:
          info['seeds'] = len(chain['peers']['seeds'])
        
        if 'persistent_peers' in chain['peers']:
          info['persistent_peers'] = len(chain['peers']['persistent_peers'])
      
      if 'apis' in chain:
        info['rpcs'] = len(chain['apis']['rpc'])
        info['apis'] = len(chain['apis']['rest'])

        for rpc in chain['apis']['rpc']:
          try:
            response = requests.get("{}/status".format(rpc['address']))
            status = response.json()
            latest_block_height = int(status['result']['sync_info']['latest_block_height'])

            earliest_block_height = int(status['result']['sync_info']['earliest_block_height'])
            latest_block_time = int(time.mktime(parser.parse(status['result']['sync_info']['latest_block_time']).timetuple()))
            earliest_block_time = int(time.mktime(parser.parse(status['result']['sync_info']['earliest_block_time']).timetuple()))
            
            info['block_height'] = latest_block_height
            info['block_speed'] = (latest_block_time - earliest_block_time) / (latest_block_height - earliest_block_height)
            break
          except:
            print("could not request rpc {}, trying next one".format(rpc['address']))
            pass

      if len(assetlist['assets']) > 0:
        if 'coingecko_id' in assetlist['assets'][0]:
            while True:
              response = None
              try:
                response = requests.get("https://api.coingecko.com/api/v3/coins/{}".format(assetlist['assets'][0]['coingecko_id']))

                coin = response.json()
                info['usd_price'] = coin['market_data']['current_price']['usd']
                info['usd_market_cap'] = coin['market_data']['market_cap']['usd']
                info['usd_fully_diluted_valuation'] = coin['market_data']['fully_diluted_valuation']['usd']
                info['usd_24h_volume'] = coin['market_data']['total_volume']['usd']
                break
              except:
                if response.status_code == 429:
                  print("got 429 retrying in 10sec")
                  time.sleep(10)
                else:
                  break

      for ibc in ibc_chains:
        if chain['chain_id'] == ibc['network_id']:
          info['ibc_30d_volume'] = ibc['blockchain_switched_stats'][0]['ibc_cashflow']
          info['ibc_30d_transfers'] = ibc['blockchain_switched_stats'][0]['ibc_transfers']
          info['30d_txs'] = ibc['blockchain_stats'][0]['txs']
          info['30d_active_addresses'] = ibc['blockchain_stats'][0]['active_addresses_cnt']
          break

      print("{}/{} - {}".format(i+1, len(chains), ','.join(map(str, list(info.values())))))
      writer.writerow(list(info.values()))
      time.sleep(5)

print('done')
