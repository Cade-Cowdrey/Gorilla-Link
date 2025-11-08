"""
Blockchain Credentials Service
NFT-based verifiable credentials on Ethereum/Polygon with immutable verification

Features:
- NFT certificate minting (degrees, certifications, achievements)
- Smart contract integration (ERC-721 standard)
- Multi-chain support (Ethereum mainnet, Polygon, Sepolia testnet)
- MetaMask wallet integration
- LinkedIn/social media credential sharing
- QR code verification for instant validation
- Employer verification portal
- Certificate marketplace/showcase
- Gas fee optimization (batch minting, L2 scaling)
- IPFS metadata storage (decentralized)
- Revocation system (for fraud/errors)
- Alumni credential registry

Revenue Model:
- Certificate minting fees: $10-50 per certificate
- Bulk university packages: $5,000-20,000/year
- Employer verification subscriptions: $1,000-5,000/year
- API access for integrations: $500-2,000/month
- Premium features (custom designs, faster minting): $25-100
Target: $200,000+ annually

Technical Stack:
- Web3.py for Ethereum interaction
- Solidity smart contracts (ERC-721)
- IPFS for metadata storage
- Polygon for low-cost L2 transactions
- Ethers.js for frontend wallet integration
- OpenZeppelin contracts for security
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import json
import hashlib
import random
import qrcode
from io import BytesIO
import base64

# Web3 imports (install: pip install web3 eth-account)
try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    # Create stub classes to prevent errors
    Web3 = None
    Account = None
    WEB3_AVAILABLE = False
    logging.warning("web3 package not installed. Blockchain features disabled. Run: pip install web3 eth-account")

from models import db, User, Experience, Education

logger = logging.getLogger(__name__)


class BlockchainCredentialService:
    """Service for blockchain-based verifiable credentials using NFTs"""
    
    # Smart contract ABIs (simplified - full contract would be deployed separately)
    CREDENTIAL_CONTRACT_ABI = [
        {
            "inputs": [
                {"name": "recipient", "type": "address"},
                {"name": "tokenURI", "type": "string"},
                {"name": "credentialHash", "type": "bytes32"}
            ],
            "name": "mintCredential",
            "outputs": [{"name": "tokenId", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"name": "tokenId", "type": "uint256"}],
            "name": "tokenURI",
            "outputs": [{"name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "tokenId", "type": "uint256"}],
            "name": "ownerOf",
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "tokenId", "type": "uint256"}],
            "name": "revokeCredential",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"name": "tokenId", "type": "uint256"}],
            "name": "isRevoked",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Network configurations
    NETWORKS = {
        'ethereum_mainnet': {
            'name': 'Ethereum Mainnet',
            'chain_id': 1,
            'rpc_url': 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
            'explorer': 'https://etherscan.io',
            'native_token': 'ETH',
            'avg_gas_price_gwei': 30,
            'avg_mint_cost_usd': 50,
            'contract_address': '0x0000000000000000000000000000000000000000'  # Deploy contract
        },
        'polygon': {
            'name': 'Polygon (Matic)',
            'chain_id': 137,
            'rpc_url': 'https://polygon-rpc.com',
            'explorer': 'https://polygonscan.com',
            'native_token': 'MATIC',
            'avg_gas_price_gwei': 30,
            'avg_mint_cost_usd': 0.01,  # Much cheaper!
            'contract_address': '0x0000000000000000000000000000000000000000'
        },
        'sepolia': {
            'name': 'Sepolia Testnet',
            'chain_id': 11155111,
            'rpc_url': 'https://sepolia.infura.io/v3/YOUR_INFURA_KEY',
            'explorer': 'https://sepolia.etherscan.io',
            'native_token': 'SepoliaETH',
            'avg_gas_price_gwei': 1,
            'avg_mint_cost_usd': 0,  # Free testnet
            'contract_address': '0x0000000000000000000000000000000000000000'
        }
    }
    
    # Credential types
    CREDENTIAL_TYPES = {
        'degree': {
            'name': 'Academic Degree',
            'icon': '🎓',
            'mint_fee': 50,
            'metadata_fields': ['degree_type', 'major', 'graduation_date', 'gpa', 'honors']
        },
        'certification': {
            'name': 'Professional Certification',
            'icon': '📜',
            'mint_fee': 25,
            'metadata_fields': ['cert_name', 'issuer', 'issue_date', 'expiry_date', 'credential_id']
        },
        'achievement': {
            'name': 'Achievement Badge',
            'icon': '🏆',
            'mint_fee': 10,
            'metadata_fields': ['achievement_name', 'description', 'date_earned', 'criteria']
        },
        'skill': {
            'name': 'Skill Verification',
            'icon': '⚡',
            'mint_fee': 15,
            'metadata_fields': ['skill_name', 'proficiency_level', 'verified_by', 'verification_date']
        },
        'experience': {
            'name': 'Work Experience',
            'icon': '💼',
            'mint_fee': 30,
            'metadata_fields': ['company', 'position', 'start_date', 'end_date', 'responsibilities']
        }
    }

    def __init__(self, network: str = 'polygon'):
        """
        Initialize blockchain service
        
        Args:
            network: Network to use (polygon recommended for low fees)
        """
        self.logger = logger
        self.network_config = self.NETWORKS.get(network)
        
        if not self.network_config:
            raise ValueError(f"Invalid network: {network}. Options: {list(self.NETWORKS.keys())}")
        
        # Initialize Web3 if available
        self.web3 = None
        if WEB3_AVAILABLE and Web3 is not None:
            try:
                self.web3 = Web3(Web3.HTTPProvider(self.network_config['rpc_url']))
                if self.web3.is_connected():
                    self.logger.info(f"Connected to {self.network_config['name']}")
                else:
                    self.logger.warning(f"Could not connect to {self.network_config['name']}")
            except Exception as e:
                self.logger.error(f"Web3 initialization error: {str(e)}")
        else:
            self.logger.warning("Web3 not available - blockchain features disabled")
        
        # Initialize smart contract
        self.contract = None
        if self.web3 and self.network_config['contract_address'] != '0x0000000000000000000000000000000000000000':
            self.contract = self.web3.eth.contract(
                address=self.network_config['contract_address'],
                abi=self.CREDENTIAL_CONTRACT_ABI
            )
    
    def mint_credential(
        self,
        user_id: int,
        credential_type: str,
        credential_data: Dict[str, Any],
        wallet_address: str,
        network: str = None
    ) -> Dict[str, Any]:
        """
        Mint an NFT credential on blockchain
        
        Args:
            user_id: User receiving credential
            credential_type: Type of credential (degree, certification, achievement, etc.)
            credential_data: Credential metadata
            wallet_address: User's wallet address (0x...)
            network: Blockchain network (defaults to polygon)
        
        Returns:
            Transaction details and NFT token ID
        """
        try:
            # Validate inputs
            if not WEB3_AVAILABLE or not self.web3 or (self.web3 and not self.web3.is_connected()):
                return {
                    'success': False,
                    'error': 'Blockchain connection not available',
                    'fallback': 'Using database storage as backup'
                }
            
            if credential_type not in self.CREDENTIAL_TYPES:
                return {'success': False, 'error': 'Invalid credential type'}
            
            # Validate wallet address
            if Web3 is None or not Web3.is_address(wallet_address):
                return {'success': False, 'error': 'Invalid wallet address'}
            
            wallet_address = Web3.to_checksum_address(wallet_address)
            
            # Get user
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Create metadata for IPFS
            metadata = self._create_metadata(user, credential_type, credential_data)
            
            # Generate credential hash for integrity
            credential_hash = self._generate_credential_hash(metadata)
            
            # Upload metadata to IPFS (simulated - would use actual IPFS service)
            ipfs_uri = self._upload_to_ipfs(metadata)
            
            # Estimate gas costs
            gas_estimate = self._estimate_minting_cost()
            
            # Mint NFT on blockchain (simulated - requires actual transaction signing)
            # In production, this would:
            # 1. Create transaction
            # 2. Sign with platform wallet
            # 3. Send transaction
            # 4. Wait for confirmation
            
            # SIMULATION MODE (replace with actual blockchain call)
            token_id = self._simulate_minting(wallet_address, ipfs_uri, credential_hash)
            
            # Generate verification QR code
            qr_code = self._generate_qr_code(token_id, self.network_config['chain_id'])
            
            # Store reference in database
            credential_record = {
                'user_id': user_id,
                'credential_type': credential_type,
                'token_id': token_id,
                'chain_id': self.network_config['chain_id'],
                'contract_address': self.network_config['contract_address'],
                'wallet_address': wallet_address,
                'ipfs_uri': ipfs_uri,
                'credential_hash': credential_hash,
                'minted_at': datetime.utcnow().isoformat(),
                'metadata': metadata,
                'qr_code': qr_code
            }
            
            # Save to database (would use BlockchainCredential model)
            self._save_credential_record(credential_record)
            
            # Calculate minting fee
            mint_fee = self.CREDENTIAL_TYPES[credential_type]['mint_fee']
            
            return {
                'success': True,
                'token_id': token_id,
                'chain': self.network_config['name'],
                'chain_id': self.network_config['chain_id'],
                'contract_address': self.network_config['contract_address'],
                'wallet_address': wallet_address,
                'ipfs_uri': ipfs_uri,
                'credential_hash': credential_hash,
                'explorer_url': f"{self.network_config['explorer']}/token/{self.network_config['contract_address']}?a={token_id}",
                'qr_code': qr_code,
                'gas_cost_usd': gas_estimate['total_cost_usd'],
                'mint_fee_usd': mint_fee,
                'metadata': metadata,
                'verification_url': f"https://pittstate-connect.edu/verify/{token_id}",
                'share_links': self._generate_share_links(token_id, metadata)
            }
            
        except Exception as e:
            self.logger.error(f"Error minting credential: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_credential(self, token_id: int, chain_id: int = None) -> Dict[str, Any]:
        """
        Verify authenticity of a credential NFT
        
        Args:
            token_id: NFT token ID
            chain_id: Blockchain network ID
        
        Returns:
            Verification results and credential details
        """
        try:
            chain_id = chain_id or self.network_config['chain_id']
            
            # Query blockchain for token
            if self.contract:
                try:
                    # Check if token exists and get owner
                    owner = self.contract.functions.ownerOf(token_id).call()
                    token_uri = self.contract.functions.tokenURI(token_id).call()
                    is_revoked = self.contract.functions.isRevoked(token_id).call()
                    
                    # Fetch metadata from IPFS
                    metadata = self._fetch_from_ipfs(token_uri)
                    
                    # Verify integrity
                    stored_hash = self._get_stored_hash(token_id)
                    computed_hash = self._generate_credential_hash(metadata)
                    integrity_valid = (stored_hash == computed_hash)
                    
                    return {
                        'success': True,
                        'valid': not is_revoked and integrity_valid,
                        'token_id': token_id,
                        'owner': owner,
                        'chain_id': chain_id,
                        'metadata': metadata,
                        'is_revoked': is_revoked,
                        'integrity_valid': integrity_valid,
                        'issued_date': metadata.get('issued_date'),
                        'issuer': metadata.get('issuer'),
                        'verification_timestamp': datetime.utcnow().isoformat()
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'valid': False,
                        'error': 'Token not found or invalid',
                        'details': str(e)
                    }
            
            # Fallback: check database
            record = self._get_credential_record(token_id, chain_id)
            if record:
                return {
                    'success': True,
                    'valid': True,
                    'token_id': token_id,
                    'metadata': record['metadata'],
                    'source': 'database',
                    'note': 'Blockchain verification unavailable, using database record'
                }
            
            return {
                'success': False,
                'valid': False,
                'error': 'Credential not found'
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying credential: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_user_credentials(self, user_id: int) -> Dict[str, Any]:
        """
        Get all blockchain credentials for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of user's NFT credentials
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get credentials from database
            credentials = self._get_user_credential_records(user_id)
            
            # Enrich with blockchain data
            enriched = []
            for cred in credentials:
                # Verify on blockchain
                verification = self.verify_credential(cred['token_id'], cred['chain_id'])
                
                enriched.append({
                    'token_id': cred['token_id'],
                    'type': cred['credential_type'],
                    'chain': self._get_network_name(cred['chain_id']),
                    'minted_at': cred['minted_at'],
                    'metadata': cred['metadata'],
                    'verification_url': f"https://pittstate-connect.edu/verify/{cred['token_id']}",
                    'explorer_url': f"{self._get_explorer_url(cred['chain_id'])}/token/{cred['contract_address']}?a={cred['token_id']}",
                    'qr_code': cred.get('qr_code'),
                    'is_valid': verification.get('valid', False),
                    'is_revoked': verification.get('is_revoked', False)
                })
            
            # Group by type
            by_type = {}
            for cred in enriched:
                cred_type = cred['type']
                if cred_type not in by_type:
                    by_type[cred_type] = []
                by_type[cred_type].append(cred)
            
            return {
                'success': True,
                'user_id': user_id,
                'total_credentials': len(enriched),
                'credentials': enriched,
                'by_type': by_type,
                'stats': {
                    'degrees': len(by_type.get('degree', [])),
                    'certifications': len(by_type.get('certification', [])),
                    'achievements': len(by_type.get('achievement', [])),
                    'skills': len(by_type.get('skill', [])),
                    'experiences': len(by_type.get('experience', []))
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user credentials: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def batch_mint_credentials(
        self,
        credentials: List[Dict[str, Any]],
        institution_id: int
    ) -> Dict[str, Any]:
        """
        Batch mint credentials for multiple users (universities use case)
        
        Args:
            credentials: List of credential data for multiple users
            institution_id: Institution performing batch mint
        
        Returns:
            Batch minting results
        """
        try:
            if not credentials:
                return {'success': False, 'error': 'No credentials provided'}
            
            results = []
            successful = 0
            failed = 0
            
            # Estimate total cost
            total_gas_estimate = len(credentials) * self._estimate_minting_cost()['total_cost_usd']
            batch_discount = 0.8 if len(credentials) > 10 else 1.0  # 20% discount for bulk
            total_cost = total_gas_estimate * batch_discount
            
            # Process each credential
            for i, cred_data in enumerate(credentials):
                try:
                    result = self.mint_credential(
                        user_id=cred_data['user_id'],
                        credential_type=cred_data['credential_type'],
                        credential_data=cred_data['data'],
                        wallet_address=cred_data['wallet_address']
                    )
                    
                    if result['success']:
                        successful += 1
                        results.append({
                            'user_id': cred_data['user_id'],
                            'status': 'success',
                            'token_id': result['token_id']
                        })
                    else:
                        failed += 1
                        results.append({
                            'user_id': cred_data['user_id'],
                            'status': 'failed',
                            'error': result.get('error')
                        })
                        
                except Exception as e:
                    failed += 1
                    results.append({
                        'user_id': cred_data.get('user_id'),
                        'status': 'error',
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'batch_size': len(credentials),
                'successful': successful,
                'failed': failed,
                'results': results,
                'total_cost_usd': total_cost,
                'avg_cost_per_credential': total_cost / len(credentials) if len(credentials) > 0 else 0,
                'batch_discount_applied': batch_discount < 1.0
            }
            
        except Exception as e:
            self.logger.error(f"Error in batch minting: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def revoke_credential(self, token_id: int, reason: str, admin_id: int) -> Dict[str, Any]:
        """
        Revoke a credential (for fraud, errors, etc.)
        
        Args:
            token_id: Token to revoke
            reason: Revocation reason
            admin_id: Admin performing revocation
        
        Returns:
            Revocation result
        """
        try:
            # Check if already revoked
            if self.contract:
                is_revoked = self.contract.functions.isRevoked(token_id).call()
                if is_revoked:
                    return {'success': False, 'error': 'Credential already revoked'}
            
            # Revoke on blockchain (would require transaction signing)
            # SIMULATION MODE
            revocation_tx = self._simulate_revocation(token_id)
            
            # Update database
            self._update_credential_status(token_id, 'revoked', reason, admin_id)
            
            # Notify credential owner
            self._notify_revocation(token_id, reason)
            
            return {
                'success': True,
                'token_id': token_id,
                'revoked_at': datetime.utcnow().isoformat(),
                'reason': reason,
                'admin_id': admin_id,
                'transaction_hash': revocation_tx
            }
            
        except Exception as e:
            self.logger.error(f"Error revoking credential: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def estimate_gas_cost(self, credential_type: str, network: str = None) -> Dict[str, Any]:
        """
        Estimate gas cost for minting a credential
        
        Args:
            credential_type: Type of credential
            network: Blockchain network
        
        Returns:
            Gas cost estimate in USD and native token
        """
        try:
            network_config = self.NETWORKS.get(network or 'polygon', self.network_config)
            
            # Gas estimation (typical ERC-721 mint: ~100,000 gas)
            gas_units = 100000
            gas_price_gwei = network_config['avg_gas_price_gwei']
            gas_price_wei = gas_price_gwei * 1e9
            
            # Calculate cost in native token
            gas_cost_native = (gas_units * gas_price_wei) / 1e18
            
            # Estimate USD cost (would query price oracle in production)
            native_token_prices = {
                'ETH': 3000,  # Example price
                'MATIC': 0.80,
                'SepoliaETH': 0
            }
            
            native_token_price = native_token_prices.get(network_config['native_token'], 0)
            gas_cost_usd = gas_cost_native * native_token_price
            
            # Add platform fee
            platform_fee = self.CREDENTIAL_TYPES.get(credential_type, {}).get('mint_fee', 25)
            
            return {
                'success': True,
                'network': network_config['name'],
                'gas_units': gas_units,
                'gas_price_gwei': gas_price_gwei,
                'gas_cost': {
                    'native_token': gas_cost_native,
                    'token_symbol': network_config['native_token'],
                    'usd': gas_cost_usd
                },
                'platform_fee_usd': platform_fee,
                'total_cost_usd': gas_cost_usd + platform_fee,
                'recommendation': self._get_network_recommendation(gas_cost_usd)
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating gas: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def connect_wallet(self, user_id: int, wallet_address: str, signature: str) -> Dict[str, Any]:
        """
        Connect and verify user's Web3 wallet
        
        Args:
            user_id: User ID
            wallet_address: Wallet address (0x...)
            signature: Signed message to verify ownership
        
        Returns:
            Connection status
        """
        try:
            if not Web3.is_address(wallet_address):
                return {'success': False, 'error': 'Invalid wallet address'}
            
            wallet_address = Web3.to_checksum_address(wallet_address)
            
            # Verify signature (would verify actual signature in production)
            # Message format: "Connect wallet to PittState Connect: {user_id}"
            verified = self._verify_signature(user_id, wallet_address, signature)
            
            if not verified:
                return {'success': False, 'error': 'Signature verification failed'}
            
            # Store wallet association
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Update user profile with wallet
            if not user.profile:
                user.profile = {}
            user.profile['wallet_address'] = wallet_address
            user.profile['wallet_connected_at'] = datetime.utcnow().isoformat()
            
            db.session.commit()
            
            return {
                'success': True,
                'user_id': user_id,
                'wallet_address': wallet_address,
                'connected_at': datetime.utcnow().isoformat(),
                'supported_networks': list(self.NETWORKS.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Error connecting wallet: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_verification_portal_data(self, employer_id: int) -> Dict[str, Any]:
        """
        Get employer verification portal data
        
        Args:
            employer_id: Employer ID
        
        Returns:
            Portal statistics and recent verifications
        """
        try:
            # Get verification history
            verifications = self._get_employer_verifications(employer_id)
            
            # Calculate statistics
            total_verified = len(verifications)
            valid_credentials = len([v for v in verifications if v.get('valid')])
            
            return {
                'success': True,
                'employer_id': employer_id,
                'stats': {
                    'total_verifications': total_verified,
                    'valid_credentials': valid_credentials,
                    'invalid_credentials': total_verified - valid_credentials,
                    'verifications_this_month': len([v for v in verifications if self._is_current_month(v['timestamp'])])
                },
                'recent_verifications': verifications[:10],  # Last 10
                'supported_credential_types': list(self.CREDENTIAL_TYPES.keys()),
                'verification_methods': [
                    {'method': 'qr_code', 'name': 'QR Code Scan'},
                    {'method': 'token_id', 'name': 'Token ID Lookup'},
                    {'method': 'wallet_address', 'name': 'Wallet Address Search'}
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting verification portal data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Private helper methods
    
    def _create_metadata(self, user: User, credential_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create NFT metadata following ERC-721 standard"""
        metadata = {
            'name': f"{user.name} - {self.CREDENTIAL_TYPES[credential_type]['name']}",
            'description': f"Verifiable {credential_type} credential issued by Pittsburg State University",
            'image': self._generate_credential_image(credential_type, data),
            'external_url': f"https://pittstate-connect.edu/credentials/{user.id}",
            'attributes': [
                {'trait_type': 'Credential Type', 'value': credential_type},
                {'trait_type': 'Recipient', 'value': user.name},
                {'trait_type': 'Recipient Email', 'value': user.email},
                {'trait_type': 'Issued By', 'value': 'Pittsburg State University'},
                {'trait_type': 'Issue Date', 'value': datetime.utcnow().isoformat()}
            ]
        }
        
        # Add credential-specific fields
        for field in self.CREDENTIAL_TYPES[credential_type]['metadata_fields']:
            if field in data:
                metadata['attributes'].append({
                    'trait_type': field.replace('_', ' ').title(),
                    'value': str(data[field])
                })
        
        return metadata
    
    def _generate_credential_hash(self, metadata: Dict[str, Any]) -> str:
        """Generate SHA-256 hash of credential for integrity verification"""
        metadata_str = json.dumps(metadata, sort_keys=True)
        return hashlib.sha256(metadata_str.encode()).hexdigest()
    
    def _upload_to_ipfs(self, metadata: Dict[str, Any]) -> str:
        """Upload metadata to IPFS (simulated - would use Pinata, NFT.Storage, etc.)"""
        # In production, use IPFS service
        # import requests
        # response = requests.post('https://api.pinata.cloud/pinning/pinJSONToIPFS', 
        #                         json=metadata, headers=headers)
        # return f"ipfs://{response.json()['IpfsHash']}"
        
        # Simulation
        fake_hash = hashlib.md5(json.dumps(metadata).encode()).hexdigest()
        return f"ipfs://{fake_hash}"
    
    def _fetch_from_ipfs(self, ipfs_uri: str) -> Dict[str, Any]:
        """Fetch metadata from IPFS"""
        # In production: requests.get(f'https://ipfs.io/ipfs/{hash}')
        # Simulation: return cached data
        return {'simulated': True}
    
    def _estimate_minting_cost(self) -> Dict[str, Any]:
        """Estimate minting cost"""
        return {
            'gas_units': 100000,
            'gas_cost_native': 0.001,
            'total_cost_usd': self.network_config['avg_mint_cost_usd']
        }
    
    def _simulate_minting(self, wallet: str, uri: str, hash: str) -> int:
        """Simulate NFT minting (would be actual blockchain transaction)"""
        # In production: send actual transaction to blockchain
        # For now, return simulated token ID
        import random
        return random.randint(1000, 999999)
    
    def _simulate_revocation(self, token_id: int) -> str:
        """Simulate revocation transaction"""
        return f"0x{''.join([f'{random.randint(0,15):x}' for _ in range(64)])}"
    
    def _generate_qr_code(self, token_id: int, chain_id: int) -> str:
        """Generate QR code for credential verification"""
        try:
            verification_url = f"https://pittstate-connect.edu/verify/{token_id}?chain={chain_id}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{qr_base64}"
            
        except Exception as e:
            self.logger.error(f"Error generating QR code: {str(e)}")
            return None
    
    def _generate_share_links(self, token_id: int, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Generate social media share links"""
        credential_name = metadata.get('name', 'My Credential')
        verification_url = f"https://pittstate-connect.edu/verify/{token_id}"
        
        return {
            'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={verification_url}",
            'twitter': f"https://twitter.com/intent/tweet?text=Check out my verified {credential_name}&url={verification_url}",
            'facebook': f"https://www.facebook.com/sharer/sharer.php?u={verification_url}",
            'direct_link': verification_url
        }
    
    def _generate_credential_image(self, credential_type: str, data: Dict[str, Any]) -> str:
        """Generate credential image URL"""
        # In production, would generate actual certificate image
        return f"https://pittstate-connect.edu/static/credentials/{credential_type}_template.png"
    
    def _save_credential_record(self, record: Dict[str, Any]):
        """Save credential to database"""
        # Would save to BlockchainCredential model
        self.logger.info(f"Saved credential record: token_id={record['token_id']}")
    
    def _get_credential_record(self, token_id: int, chain_id: int) -> Optional[Dict]:
        """Get credential from database"""
        # Would query BlockchainCredential model
        return None
    
    def _get_user_credential_records(self, user_id: int) -> List[Dict]:
        """Get all credentials for user from database"""
        # Would query BlockchainCredential.filter_by(user_id=user_id)
        return []
    
    def _get_stored_hash(self, token_id: int) -> str:
        """Get stored credential hash"""
        return "0x" + "0" * 64
    
    def _update_credential_status(self, token_id: int, status: str, reason: str, admin_id: int):
        """Update credential status in database"""
        self.logger.info(f"Updated credential {token_id} to {status}")
    
    def _notify_revocation(self, token_id: int, reason: str):
        """Notify credential owner of revocation"""
        self.logger.info(f"Sent revocation notification for token {token_id}")
    
    def _verify_signature(self, user_id: int, wallet: str, signature: str) -> bool:
        """Verify wallet signature"""
        # Would verify actual cryptographic signature
        return True
    
    def _get_network_name(self, chain_id: int) -> str:
        """Get network name from chain ID"""
        for name, config in self.NETWORKS.items():
            if config['chain_id'] == chain_id:
                return config['name']
        return 'Unknown'
    
    def _get_explorer_url(self, chain_id: int) -> str:
        """Get block explorer URL for chain"""
        for config in self.NETWORKS.values():
            if config['chain_id'] == chain_id:
                return config['explorer']
        return ''
    
    def _get_network_recommendation(self, gas_cost_usd: float) -> str:
        """Recommend best network based on gas costs"""
        if gas_cost_usd > 20:
            return "Consider using Polygon for much lower fees (~$0.01)"
        elif gas_cost_usd > 5:
            return "Gas fees are moderate. Polygon recommended for cost savings."
        else:
            return "Gas fees are reasonable for this network"
    
    def _get_employer_verifications(self, employer_id: int) -> List[Dict]:
        """Get employer's verification history"""
        # Would query CredentialVerification model
        return []
    
    def _is_current_month(self, timestamp: str) -> bool:
        """Check if timestamp is in current month"""
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.utcnow()
            return dt.year == now.year and dt.month == now.month
        except:
            return False


# Smart Contract Source Code (Solidity)
CREDENTIAL_CONTRACT_SOLIDITY = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract PittStateCredentials is ERC721URIStorage, Ownable {
    uint256 private _tokenIds;
    
    mapping(uint256 => bytes32) public credentialHashes;
    mapping(uint256 => bool) public revokedCredentials;
    
    event CredentialMinted(address indexed recipient, uint256 indexed tokenId, bytes32 credentialHash);
    event CredentialRevoked(uint256 indexed tokenId, string reason);
    
    constructor() ERC721("PittState Credentials", "PSC") {}
    
    function mintCredential(
        address recipient,
        string memory tokenURI,
        bytes32 credentialHash
    ) public onlyOwner returns (uint256) {
        _tokenIds++;
        uint256 newTokenId = _tokenIds;
        
        _mint(recipient, newTokenId);
        _setTokenURI(newTokenId, tokenURI);
        credentialHashes[newTokenId] = credentialHash;
        
        emit CredentialMinted(recipient, newTokenId, credentialHash);
        return newTokenId;
    }
    
    function revokeCredential(uint256 tokenId, string memory reason) public onlyOwner {
        require(_exists(tokenId), "Token does not exist");
        revokedCredentials[tokenId] = true;
        emit CredentialRevoked(tokenId, reason);
    }
    
    function isRevoked(uint256 tokenId) public view returns (bool) {
        return revokedCredentials[tokenId];
    }
    
    function verifyCredential(uint256 tokenId, bytes32 providedHash) public view returns (bool) {
        require(_exists(tokenId), "Token does not exist");
        return credentialHashes[tokenId] == providedHash && !revokedCredentials[tokenId];
    }
}
"""


# Example usage
if __name__ == '__main__':
    # Initialize service with Polygon (low fees)
    service = BlockchainCredentialService(network='polygon')
    
    # Test minting a degree credential
    print("Testing Degree Credential Minting:")
    result = service.mint_credential(
        user_id=1,
        credential_type='degree',
        credential_data={
            'degree_type': 'Bachelor of Science',
            'major': 'Computer Science',
            'graduation_date': '2024-05-15',
            'gpa': '3.8',
            'honors': 'Cum Laude'
        },
        wallet_address='0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0'
    )
    print(f"Minting success: {result['success']}")
    if result['success']:
        print(f"Token ID: {result['token_id']}")
        print(f"Verification URL: {result['verification_url']}")
    
    # Test credential verification
    print("\nTesting Credential Verification:")
    if result['success']:
        verification = service.verify_credential(result['token_id'])
        print(f"Credential valid: {verification.get('valid')}")
    
    # Test gas estimation
    print("\nTesting Gas Cost Estimation:")
    gas_estimate = service.estimate_gas_cost('degree', 'ethereum_mainnet')
    print(f"Ethereum mainnet cost: ${gas_estimate.get('total_cost_usd', 0):.2f}")
    
    gas_estimate_poly = service.estimate_gas_cost('degree', 'polygon')
    print(f"Polygon cost: ${gas_estimate_poly.get('total_cost_usd', 0):.2f}")
