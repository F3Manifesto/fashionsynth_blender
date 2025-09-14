INFURA_GATEWAY = "https://thedial.infura-ipfs.io/ipfs/"


HOODIE_DEFAULTS = {
   "front_panel": {
        "ipfs": "QmWwRYcuyNeXzNFbFHn6NomxerQJH7gpdv337uNkygvS3u",
        "quantity": 1,
        "display_name": "Front Panel",
        "description": "Front panel pattern piece for hoodie with fold cutting line"
    },
  "back_panel":  {
        "ipfs": "QmYpqS8Bvooy8VZuyYB4QCa4AEzyiKYaevLZxTMdSKQ8LW",
        "quantity": 1,
        "display_name": "Back Panel",
        "description": "Back panel pattern piece for hoodie with fold cutting line"
    },
    "hood":  {
        "ipfs": "QmZCiFkntv59eDymtZKpLbFuy1HHVBgWk7YxJbousgUhmE",
        "quantity": 2,
        "display_name": "Hood",
        "description": "Hood pattern piece for hoodie"
    },
      "pocket":  {
        "ipfs": "QmeRcLaAJt2tMEtc6fQs4awzZJHPLUGkGsk7sM4FijBa2S",
        "quantity": 1,
        "display_name": "Pocket",
        "description": "Pocket pattern piece for hoodie"
    },
      "sleeve_cuff":  {
        "ipfs": "QmR2aM7nPH6PmswKc4115GhdxbCEhwDhFAUqXBGrDZuCws",
        "quantity": 2,
        "display_name": "Sleeve Cuff",
        "description": "Sleeve cuff pattern piece for hoodie"
    },
      "sleeve":  {
        "ipfs": "QmTEAfKjAnJ8Rm7BwgzGCtb1wE5H9J3BkSoEFgeBCeHU2a",
        "quantity": 2,
        "display_name": "Sleeve",
        "description": "Sleeve pattern piece for hoodie"
    },
      "waist_band":  {
        "ipfs": "QmZQFmPophwckf4UKDCD5YMLPeism2oYNkrgFhN33N52Q6",
        "quantity": 1,
        "display_name": "Waist Band",
        "description": "Waist band pattern piece for hoodie"
    }
}

  


TSHIRT_DEFAULTS = {
 "back_panel": {
     
       "ipfs": "QmZR3yzYnKfbMMw48E7gRG71H7VGATgF6jkm3Q8LXAYehy",
        "quantity": 1,
        "display_name": "Back Panel",
        "description": "Back panel pattern piece for t-shirt with fold cutting line"
        
     }  ,
  
  "front_panel": {
     
       "ipfs": "QmdrXEuXshhPUDUTsfHKzNVMrmQn68H4oPA92vBbLxBBa4",
        "quantity": 1,
        "display_name": "Front Panel",
        "description": "Front panel pattern piece for t-shirt with fold cutting line"
        
     } , 
 "neck_binding": {
     
       "ipfs": "QmVkhYT7SfWt4TR2gx6t9fsT76rrmqbaeZmYHLzdaSs84m",
               "quantity": 1,
        "display_name": "Neck Binding",
        "description": "Neck binding pattern piece for t-shirt collar"
        
     }  ,
 
 
 
 
 
  "sleeve": {
     
       "ipfs": "Qmd8nXv1mn2D5V3nUYxpGdPmGfksAZkRru3YtRT3Nvf58j",
        "quantity": 2,
        "display_name": "Sleeve",
        "description": "Sleeve pattern piece for t-shirt"
        
     }  


  
}

def get_garment_defaults(garment_type):
    """Get default patterns for a specific garment type"""
    garment_map = {
        "hoodie": HOODIE_DEFAULTS,
        "tshirt": TSHIRT_DEFAULTS,
    }
    return garment_map.get(garment_type, {})

def ipfs_to_gateway_url(ipfs_hash):
    """Convert IPFS hash to gateway URL"""
    if ipfs_hash.startswith("ipfs://"):
        hash_only = ipfs_hash.replace("ipfs://", "")
    else:
        hash_only = ipfs_hash
    
    return f"{INFURA_GATEWAY}{hash_only}"

def get_all_garment_types():
    """Get list of all available garment types"""
    return ["hoodie", "tshirt", "shirt"]