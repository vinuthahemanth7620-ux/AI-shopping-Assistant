import re
import json
import logging

logger = logging.getLogger(__name__)


class ProductInformationProcessor:
    """
    Product Information Processor & Category-Aware Feature Extraction Service.
    Separates Raw Database Product Data from Clean Display Product Data.
    Follows MVP Architecture.
    """

    # Low-value metadata keys to filter out
    METADATA_IGNORE_KEYS = {
        'asin', 'package dimensions', 'item weight', 'date first available',
        'country of origin', 'manufacturer', 'model number', 'shipping weight',
        'item model number', 'is discontinued by manufacturer', 'department',
        'batteries required', 'batteries included', 'import designation',
        'unspsc code', 'customer reviews', 'best sellers rank', 'generic name',
        'net quantity', 'importer', 'packer', 'included components',
        'part number', 'item package quantity', 'packaging', 'asin number',
        'upc', 'ean', 'isbn', 'unit count', 'number of items', 'shipping',
        'details', 'features', 'raw', 'info'
    }

    # Marketing phrases to remove from extracted features
    MARKETING_PHRASES = [
        'ideal gift', 'perfect gift', 'best gift', 'great gift', 'beautiful gift',
        'striking accent', 'no one denies', 'ultimate gathering spot',
        'our service', 'contact us', 'satisfactory solution', 'customer service',
        'buy with confidence', 'money back', 'guarantee', '100% satisfaction',
        'risk free', 'warranty card', 'package included', 'package contains'
    ]

    @classmethod
    def _clean_text(cls, text):
        if not text:
            return ""
        return str(text).strip()

    @classmethod
    def _get_category_name(cls, product_or_dict):
        """Extract category name from Product model or dict."""
        if hasattr(product_or_dict, 'category') and product_or_dict.category:
            return product_or_dict.category.name.lower()
        if hasattr(product_or_dict, 'category_name'):
            return str(product_or_dict.category_name).lower()
        if isinstance(product_or_dict, dict):
            cat_name = product_or_dict.get('category_name') or product_or_dict.get('category')
            if isinstance(cat_name, str):
                return cat_name.lower()
        return ""

    @classmethod
    def _get_raw_details_and_features(cls, product_or_dict):
        """
        Unpack raw specifications JSON into separate clean (details_dict, features_list).
        Handles Amazon dataset format {"details": {...}, "features": [...]} as well as direct dicts.
        """
        specs = None
        if hasattr(product_or_dict, 'specifications'):
            specs = product_or_dict.specifications
        elif isinstance(product_or_dict, dict):
            specs = product_or_dict.get('specifications')

        if isinstance(specs, str) and specs.strip():
            try:
                specs = json.loads(specs)
            except Exception:
                specs = {}

        if not isinstance(specs, dict):
            specs = {}

        details_dict = {}
        features_list = []

        if 'details' in specs and isinstance(specs['details'], dict):
            details_dict = dict(specs['details'])
        if 'features' in specs and isinstance(specs['features'], (list, tuple)):
            features_list = [str(x).strip() for x in specs['features'] if x and str(x).strip()]

        # If specs is a direct flat key-value dict without 'details'/'features' wrapper
        if not details_dict and not features_list:
            for k, v in specs.items():
                if str(k).lower() in ('details', 'features'):
                    continue
                if isinstance(v, (dict, list)):
                    continue
                details_dict[str(k)] = str(v)

        return details_dict, features_list

    @classmethod
    def extract_important_specifications(cls, product_or_dict, limit=8):
        """
        Extract a clean, high-value specifications dictionary for user display.
        Hides low-value metadata (ASIN, Package dimensions, Item model number, Date first available, etc.)
        and normalizes duplicate or redundant key/value pairs.
        """
        details_dict, _ = cls._get_raw_details_and_features(product_or_dict)
        if not details_dict:
            return {}

        clean_specs = {}
        seen_keys_lower = set()

        for k, v in details_dict.items():
            if v is None:
                continue
            clean_k = str(k).strip() if k is not None else ""
            clean_v = str(v).strip()
            if not clean_v:
                continue

            # Handle empty key '' e.g. '': 'Shape Rectangular'
            if not clean_k and ' ' in clean_v:
                parts = clean_v.split(' ', 1)
                clean_k = parts[0].strip()
                clean_v = parts[1].strip()

            if not clean_k or not clean_v:
                continue

            k_lower = clean_k.lower()
            # Skip low-value internal/packaging metadata
            if any(ignored in k_lower for ignored in cls.METADATA_IGNORE_KEYS):
                continue

            # Normalize key names
            normalized_key = clean_k.title()
            if k_lower in ['brand name', 'brand']:
                normalized_key = 'Brand'
            elif k_lower in ['material type', 'material']:
                normalized_key = 'Material'
            elif k_lower in ['special feature', 'special features']:
                normalized_key = 'Special Feature'
            elif k_lower in ['color', 'colour']:
                normalized_key = 'Color'
            elif k_lower in ['product dimensions', 'item dimensions', 'dimensions']:
                normalized_key = 'Dimensions'
            elif k_lower in ['number of pieces', 'pieces', 'package quantity', 'item package quantity']:
                normalized_key = 'Pieces'
            elif k_lower in ['item weight', 'weight']:
                normalized_key = 'Weight'

            norm_key_lower = normalized_key.lower()
            if norm_key_lower in seen_keys_lower:
                continue

            # Normalize redundant values (e.g., "Rechargeable: Rechargeable" -> "Rechargeable: Yes")
            if clean_v.lower() == norm_key_lower:
                clean_v = "Yes"

            seen_keys_lower.add(norm_key_lower)
            clean_specs[normalized_key] = clean_v

            if len(clean_specs) >= limit:
                break

        return clean_specs

    @classmethod
    def _is_duplicate_feature(cls, new_feature, existing_features):
        """Check if feature is duplicate (case-insensitive, whitespace-insensitive, or high substring overlap)."""
        clean_new = re.sub(r'[^a-z0-9]', '', str(new_feature).lower())
        if not clean_new:
            return True
        for ef in existing_features:
            clean_ef = re.sub(r'[^a-z0-9]', '', str(ef).lower())
            if clean_new == clean_ef or clean_new in clean_ef or clean_ef in clean_new:
                return True
        return False

    @classmethod
    def extract_important_features(cls, product_or_dict, limit=3):
        """
        Extract only the most relevant, high-priority features based on product category.
        Strictly relies on available database data without inventing missing specifications.
        Returns a list of clean string bullet points (max 3-4).
        """
        name = cls._clean_text(getattr(product_or_dict, 'name', '') or (product_or_dict.get('name') if isinstance(product_or_dict, dict) else ''))
        desc = cls._clean_text(getattr(product_or_dict, 'description', '') or (product_or_dict.get('description') if isinstance(product_or_dict, dict) else ''))
        brand = cls._clean_text(getattr(product_or_dict, 'brand', '') or (product_or_dict.get('brand') if isinstance(product_or_dict, dict) else ''))
        cat_name = cls._get_category_name(product_or_dict)
        details_dict, features_list = cls._get_raw_details_and_features(product_or_dict)

        combined_text = f"{name} {desc} {' '.join([f'{k}:{v}' for k,v in details_dict.items()])} {' '.join(features_list)}"

        extracted = []

        # 1. CATEGORY-SPECIFIC EXTRACTION RULES
        
        # --- LAPTOPS / COMPUTERS ---
        if any(c in cat_name or c in name.lower() for c in ['laptop', 'computer', 'notebook', 'macbook', 'chromebook']):
            cpu_m = re.search(r'\b(Intel\s+(?:Core\s+)?i[3579]|Ryzen\s+[3579]|Apple\s+M[123](?:\s+(?:Pro|Max|Ultra))?|Core\s+Ultra\s+[579])\b', combined_text, re.IGNORECASE)
            if cpu_m:
                extracted.append(f"{cpu_m.group(1).title()} Processor")

            ram_m = re.search(r'\b(\d+\s*GB)\s*(?:DDR[45]|LPDDR[45]|RAM|Memory)\b', combined_text, re.IGNORECASE)
            if ram_m:
                extracted.append(f"{ram_m.group(1).upper()} RAM")

            storage_m = re.search(r'\b(\d+\s*(?:GB|TB))\s*(?:SSD|NVMe|Storage)\b', combined_text, re.IGNORECASE)
            if storage_m:
                extracted.append(f"{storage_m.group(1).upper()} SSD Storage")

            disp_m = re.search(r'\b(\d+(?:\.\d+)?[\"\']?\s*(?:inch| OLED| Retina| FHD| QHD| 4K| 120Hz| 144Hz| 165Hz| Display))\b', combined_text, re.IGNORECASE)
            if disp_m and len(extracted) < limit:
                extracted.append(f"{disp_m.group(1).strip()} Display")

            gpu_m = re.search(r'\b(NVIDIA\s+RTX\s*\d{4}|GTX\s*\d{4}|Radeon|Iris\s+Xe|Intel\s+Arc)\b', combined_text, re.IGNORECASE)
            if gpu_m and len(extracted) < limit:
                extracted.append(f"{gpu_m.group(1).strip()} Graphics")

        # --- SMARTPHONES / MOBILE ---
        elif any(c in cat_name or c in name.lower() for c in ['smartphone', 'mobile', 'phone', 'galaxy', 'iphone', 'pixel', 'redmi', 'oneplus']):
            disp_m = re.search(r'\b(\d+(?:\.\d+)?[\"\']?\s*(?:AMOLED|OLED|120Hz|90Hz|Retina|FHD\+))\b', combined_text, re.IGNORECASE)
            if disp_m:
                extracted.append(f"{disp_m.group(1).strip()} Display")

            ram_st = re.search(r'\b(\d+\s*GB)\s*(?:RAM)?\s*[\/\+]\s*(\d+\s*(?:GB|TB))\b', combined_text, re.IGNORECASE)
            if ram_st:
                extracted.append(f"{ram_st.group(1).upper()} RAM / {ram_st.group(2).upper()} Storage")
            else:
                ram_m = re.search(r'\b(\d+\s*GB)\s*RAM\b', combined_text, re.IGNORECASE)
                if ram_m:
                    extracted.append(f"{ram_m.group(1).upper()} RAM")
                st_m = re.search(r'\b(\d+\s*(?:GB|TB))\s*(?:ROM|Storage|Internal)\b', combined_text, re.IGNORECASE)
                if st_m and len(extracted) < limit:
                    extracted.append(f"{st_m.group(1).upper()} Storage")

            cam_m = re.search(r'\b(\d+\s*MP)\s*(?:Triple|Quad|Dual|Main|Rear|Camera)?\b', combined_text, re.IGNORECASE)
            if cam_m and len(extracted) < limit:
                extracted.append(f"{cam_m.group(1).upper()} Camera")

            bat_m = re.search(r'\b(\d{4}\s*mAh)\b', combined_text, re.IGNORECASE)
            if bat_m and len(extracted) < limit:
                extracted.append(f"{bat_m.group(1).upper()} Battery")

        # --- HEADPHONES / AUDIO ---
        elif any(c in cat_name or c in name.lower() for c in ['headphone', 'earphone', 'earbud', 'audio', 'airpods', 'headset', 'speaker', 'soundbar']):
            if re.search(r'\b(ANC|Active Noise Cancel|Noise Cancel)\b', combined_text, re.IGNORECASE):
                extracted.append("Active Noise Cancellation")
            elif re.search(r'\b(ENC|Environmental Noise)\b', combined_text, re.IGNORECASE):
                extracted.append("Environmental Noise Cancellation")

            bt_m = re.search(r'\b(Bluetooth\s*v?\d+(?:\.\d+)?|Wireless|TWS)\b', combined_text, re.IGNORECASE)
            if bt_m:
                extracted.append(f"{bt_m.group(1).title()} Connectivity")

            play_m = re.search(r'\b(\d+\s*(?:Hours?|hrs?))\s*(?:Playtime|Battery|Play back|Playback)\b', combined_text, re.IGNORECASE)
            if play_m:
                extracted.append(f"Up to {play_m.group(1)} Playtime")

            driver_m = re.search(r'\b(\d+(?:\.\d+)?\s*mm)\s*(?:Driver|Dynamic Driver)\b', combined_text, re.IGNORECASE)
            if driver_m and len(extracted) < limit:
                extracted.append(f"{driver_m.group(1)} Dynamic Drivers")

        # --- INDUCTION STOVE / COOKTOP / KITCHEN APPLIANCES ---
        elif any(c in cat_name or c in name.lower() for c in ['induction', 'cooktop', 'stove', 'blender', 'air fryer', 'juicer', 'toaster']):
            power_m = re.search(r'\b(\d{3,4}\s*W(?:atts?)?)\b', combined_text, re.IGNORECASE)
            if power_m:
                extracted.append(f"{power_m.group(1).upper()} Power Output")

            mode_m = re.search(r'\b(\d+\s*(?:Preset|Cooking|Power|Temperature)?\s*(?:Modes?|Levels?|Menu))\b', combined_text, re.IGNORECASE)
            if mode_m:
                extracted.append(f"{mode_m.group(1).title()}")

            ctrl_m = re.search(r'\b(Touch Control|Push Button|Feather Touch|Digital Display|Rotary Knob)\b', combined_text, re.IGNORECASE)
            if ctrl_m and len(extracted) < limit:
                extracted.append(f"{ctrl_m.group(1).title()}")

            if re.search(r'\b(Overheat|Auto-Off|Auto Shut|Child Lock|Safety)\b', combined_text, re.IGNORECASE) and len(extracted) < limit:
                extracted.append("Auto Shut-off & Overheat Protection")

        # --- APPLIANCE / REFRIGERATOR HANDLE COVERS / HOME GOODS ---
        elif any(c in cat_name or c in name.lower() for c in ['handle cover', 'refrigerator', 'appliance cover', 'cover', 'sunflower', 'towel', 'curtain']):
            # Washable / Reusable
            if re.search(r'\b(Washable|Machine Washable|Reusable)\b', combined_text, re.IGNORECASE):
                extracted.append("Washable and Reusable")

            # Material
            mat_m = re.search(r'\b(Neoprene|Cotton|Polyester|Microfiber|Velvet|Linen)\b', combined_text, re.IGNORECASE)
            if mat_m:
                extracted.append(f"{mat_m.group(1).title()} Material")

            # Function / Protection
            if re.search(r'\b(stain|fingerprint|clean|dust|scratch|protect)\b', combined_text, re.IGNORECASE):
                extracted.append("Protects Handles from Stains & Fingerprints")

            # Pattern / Design / Pieces
            pc_m = re.search(r'\b(\d+\s*(?:PCS?|Pieces?|Set))\b', combined_text, re.IGNORECASE)
            if pc_m and len(extracted) < limit:
                extracted.append(f"{pc_m.group(1).upper()} Set")

        # --- WASHING MACHINE / LARGE APPLIANCES ---
        elif any(c in cat_name or c in name.lower() for c in ['washing machine', 'washer', 'dryer', 'fridge', 'ac', 'air conditioner']):
            cap_m = re.search(r'\b(\d+(?:\.\d+)?\s*(?:kg|Kg|Liters?|L))\b', combined_text, re.IGNORECASE)
            if cap_m:
                extracted.append(f"{cap_m.group(1)} Capacity")

            load_m = re.search(r'\b(Front Load|Top Load|Fully Automatic|Semi Automatic|Inverter|Double Door|Single Door|Split AC)\b', combined_text, re.IGNORECASE)
            if load_m:
                extracted.append(f"{load_m.group(1).title()}")

            star_m = re.search(r'\b(\d\s*Star)\b', combined_text, re.IGNORECASE)
            if star_m:
                extracted.append(f"{star_m.group(1).title()} Energy Rating")
            else:
                spin_m = re.search(r'\b(\d{3,4}\s*RPM)\b', combined_text, re.IGNORECASE)
                if spin_m and len(extracted) < limit:
                    extracted.append(f"{spin_m.group(1).upper()} Spin Speed")

        # --- SHOES / APPAREL ---
        elif any(c in cat_name or c in name.lower() for c in ['shoe', 'sneaker', 'boot', 'footwear', 'sandal', 'shirt', 'jacket', 't-shirt', 'jeans']):
            mat_m = re.search(r'\b(Leather|Mesh|Rubber Sole|EVA Sole|Canvas|Cotton|Denim|Memory Foam)\b', combined_text, re.IGNORECASE)
            if mat_m:
                extracted.append(f"{mat_m.group(1).title()} Material")

            use_m = re.search(r'\b(Running|Walking|Casual|Formal|Sports|Breathable|Cushioned)\b', combined_text, re.IGNORECASE)
            if use_m:
                extracted.append(f"Designed for {use_m.group(1).title()}")

            closure_m = re.search(r'\b(Lace-Up|Slip-On|Zipper|Velcro)\b', combined_text, re.IGNORECASE)
            if closure_m and len(extracted) < limit:
                extracted.append(f"{closure_m.group(1).title()} Style")

        # 2. RAW FEATURES LIST PROCESSOR & DEDUPLICATION
        if len(extracted) < limit and features_list:
            for feat_str in features_list:
                if len(extracted) >= limit:
                    break
                clean_f = str(feat_str).strip()
                if not clean_f:
                    continue

                # Remove marketing boilerplate phrases
                f_lower = clean_f.lower()
                if any(m in f_lower for m in cls.MARKETING_PHRASES):
                    continue

                # Split at first dash or colon if paragraph is very long
                if len(clean_f) > 60:
                    parts = re.split(r'[\:\-\|]', clean_f)
                    if len(parts[0].strip()) >= 10 and len(parts[0].strip()) <= 50:
                        clean_f = parts[0].strip()
                    else:
                        clean_f = ' '.join(clean_f.split()[:8]) + '...'

                # Remove leading/trailing bullet points or numbers
                clean_f = re.sub(r'^[•\-\*\d+\.\s]+', '', clean_f).strip()

                if clean_f and not cls._is_duplicate_feature(clean_f, extracted):
                    extracted.append(clean_f)

        # 3. CLEAN SPECIFICATIONS FALLBACK
        if len(extracted) < limit and details_dict:
            clean_specs = cls.extract_important_specifications(product_or_dict, limit=5)
            for k, v in clean_specs.items():
                if len(extracted) >= limit:
                    break
                bullet = f"{k}: {v}"
                if not cls._is_duplicate_feature(bullet, extracted):
                    extracted.append(bullet)

        # Deduplicate final features
        final_features = []
        for ef in extracted:
            if not cls._is_duplicate_feature(ef, final_features):
                final_features.append(ef)

        # If empty after all checks, provide clean brand/category summary bullet
        if not final_features:
            if brand and cat_name:
                final_features.append(f"Official {brand.title()} {cat_name.title()}")
            elif brand:
                final_features.append(f"High Quality {brand.title()} Product")
            elif name:
                final_features.append(f"{name[:40]}")

        return final_features[:max(3, limit)]

    @classmethod
    def generate_short_summary(cls, product_or_dict):
        """
        Generate a factual 1-2 sentence (15-30 words max, max 40) product summary.
        Replaces long marketing boilerplate with clean shopping summaries.
        """
        name = cls._clean_text(getattr(product_or_dict, 'name', '') or (product_or_dict.get('name') if isinstance(product_or_dict, dict) else ''))
        desc = cls._clean_text(getattr(product_or_dict, 'description', '') or (product_or_dict.get('description') if isinstance(product_or_dict, dict) else ''))
        brand = cls._clean_text(getattr(product_or_dict, 'brand', '') or (product_or_dict.get('brand') if isinstance(product_or_dict, dict) else ''))
        cat_name = cls._get_category_name(product_or_dict)
        details_dict, features_list = cls._get_raw_details_and_features(product_or_dict)

        # Clean raw description
        if desc:
            clean_d = re.sub(r'<[^>]+>', '', desc).strip()
            clean_d = re.sub(r'(ASIN|Package Dimensions|Date First Available|Item Weight|Manufacturer|Country of Origin):[^\.\n]+', '', clean_d, flags=re.IGNORECASE)
            
            first_sentence = re.split(r'[\.\!\;\n]', clean_d)[0].strip()
            if len(first_sentence) >= 20:
                words = first_sentence.split()
                if len(words) <= 35:
                    return first_sentence + ("." if not first_sentence.endswith(".") else "")
                else:
                    return ' '.join(words[:28]) + '...'

        # Synthesize from features or specifications if available
        if features_list and len(features_list[0]) >= 15:
            feat_sentence = re.split(r'[\.\!\;\n]', features_list[0])[0].strip()
            feat_sentence = re.sub(r'^[•\-\*\d+\.\s]+', '', feat_sentence)
            words = feat_sentence.split()
            if len(words) >= 5 and len(words) <= 35:
                return f"{name} - {feat_sentence}" + ("." if not feat_sentence.endswith(".") else "")

        # Fallback generator based on Name, Brand, Category
        category_title = cat_name.title() if cat_name else "Product"
        brand_title = brand.title() if brand else ""
        
        if brand_title:
            return f"High-quality {brand_title} {category_title} designed for reliable everyday use and quality performance."
        return f"{name} delivering essential features and quality performance for your shopping needs."

    @classmethod
    def process_product(cls, product_or_dict):
        """
        Process product and return display-ready summary dictionary.
        Returns:
        {
            'short_description': '1-2 sentence summary',
            'important_features': ['Feature 1', 'Feature 2', 'Feature 3']
        }
        """
        features = cls.extract_important_features(product_or_dict, limit=3)
        summary = cls.generate_short_summary(product_or_dict)
        return {
            'short_description': summary,
            'important_features': features
        }
