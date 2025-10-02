# API Call Extraction Fix - Summary

## Problem

The route analysis was extracting ALL API calls from ALL imported components and Vuex store modules, not just the ones actually used by each component. This made the analysis too large and inaccurate.

### Specific Issues:

1. **Store Action Parsing Bug**: When parsing Vuex store actions, the regex pattern was incomplete, causing it to extract ALL actions from the entire store file instead of just the specific action being dispatched.

2. **Duplicate Extraction**: Components were showing API calls from:
   - Their own code
   - All child components' API calls
   - All API calls from the entire Vuex store module

### Example:
- `index.vue` dispatches 3 store actions but was showing 19 API calls
- `garmentSelect.vue` dispatches 1 action but was showing 4 API calls

## Root Cause

In `analyzers/vue_parser.py`, the `_parse_store_action` method had a flawed regex pattern:

**OLD (Broken)**:
```python
action_pattern = rf'(?:async\s+)?{re.escape(action_name)}\s*\(\s*\{{[^}}]*\}}'
```

This pattern only matched:
```javascript
async getBinId({ commit }   // STOPS HERE - missing ", payload) {"
```

When it should match:
```javascript
async getBinId({ commit }, payload) {  // COMPLETE FUNCTION SIGNATURE
```

Because the pattern stopped early, the brace tracking started from the wrong position and extracted ALL remaining actions in the file instead of just the one function body.

## Solution

### Fixed Regex Pattern:
```python
action_pattern = rf'(?:async\s+)?{re.escape(action_name)}\s*\([^)]*\)\s*{{'
```

This correctly matches the complete function signature including parameters:
```javascript
async getBinId({ commit }, payload) {
```

### Fixed Brace Tracking:
```python
# The match includes the opening brace, so start after it
opening_brace_pos = action_match.group().rfind('{')
start_pos = action_match.start() + opening_brace_pos + 1

# Then track braces properly to find just this function's body
brace_depth = 1
for i in range(start_pos, len(actions_content)):
    if actions_content[i] == '{':
        brace_depth += 1
    elif actions_content[i] == '}':
        brace_depth -= 1
        if brace_depth == 0:
            end_pos = i
            break
```

### Added Deduplication:
```python
dispatched_actions = set()  # Track which actions are actually dispatched

# Only parse each action once per component
action_key = f"{module_name}/{action_name}"
if action_key in dispatched_actions:
    continue
dispatched_actions.add(action_key)
```

## Results

### Before Fix:
- **Files analyzed**: 15
- **Relationships**: 120
- **Problem**: Each component showed all API calls from entire store module
- Example: `index.vue` with 3 dispatches showed 19 API calls

### After Fix:
- **Files analyzed**: 15
- **Relationships**: 38 (68% reduction)
- **Accurate**: Each component shows only its own API calls
- Example: `index.vue` with 3 dispatches now shows 3 API calls

## Example Output (Fixed)

```markdown
### index.vue
- api_post: `warehouse/cycle-count/get-bin-id`
  → Controller: `CycleCountController@getBinId`
    → Services: `CycleCountService`
- api_post: `warehouse/cycle-count/get-garment-option`
  → Controller: `CycleCountController@getGarmentOptions`
    → Services: `CycleCountService`
- api_post: `warehouse/cycle-count/get-product-option`
  → Controller: `CycleCountController@getProductOption`
    → Services: `CycleCountService`

### garmentSelect.vue
- api_post: `warehouse/cycle-count/get-start-new-bin-count-Data`
  → Controller: `CycleCountController@getStartNewBinCountData`
    → Services: `CycleCountService`
```

## Behavior

Now the analysis correctly:

1. **Only extracts API calls from store actions that are actually dispatched** by each component
2. **Parses only the specific action function body**, not the entire actions.js file
3. **Shows each component's direct API calls**, not inherited from children
4. **Deduplicates actions** within the same component
5. **Displays the complete chain**: Component → API Call → Controller → Services

## Files Modified

- `analyzers/vue_parser.py`:
  - Fixed `_parse_store_action()` regex pattern
  - Fixed brace tracking logic
  - Added action deduplication in `_get_store_api_calls()`

## Usage

```bash
# Analyze any route
python main.py analyze warehouse/cycle-count --type route --smart --output analysis.md

# Output now shows:
# - Each component with only ITS direct API calls
# - No duplication from child components or entire store modules
# - Complete chain: API → Controller → Services
# - Accurate, focused analysis
```

## Key Takeaway

The analysis is now **precise and focused**: each Vue component shows only the API calls it directly makes, giving you an accurate understanding of which component is responsible for which backend calls.
