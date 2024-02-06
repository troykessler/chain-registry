import csv

with open("chains.csv", 'r', newline='') as chains_csv:
  reader = spamreader = csv.reader(chains_csv)
  headers = next(reader)
  headers.append('score')

  with open("chains_ranked.csv", 'w', newline='') as chains_ranked_csv:
    writer = csv.writer(chains_ranked_csv)
    writer.writerow(headers)

    for row in reader:
      # peer score: (seeds + persistent_peers) * (rpcs + apis) / 100
      peer_score = ((int(row[3]) + int(row[4])) * (int(row[5]) + int(row[6]))) / 100

      # block score: (blocks / block_speed * 1000000)
      block_score = 0
      if int(row[7]) > 0 and float(row[8]) > 0:
        block_score = (float(row[8]) / int(row[7]) * 1000000)

      # market score: (market_cap + 12 * 30d_ibc_volume + 365 * 24h_volume) / 1000000
      market_score = (float(row[10]) + 12 * float(row[13]) + 365*float(row[12])) / 1000000

      # activity score: (30d_txs + 30d_active_accounts) / 100000
      activity_score = (int(row[15]) + int(row[16])) / 100000

      # get total score
      total_score = peer_score * block_score * market_score * activity_score
      row.append(str(total_score))

      writer.writerow(row)
