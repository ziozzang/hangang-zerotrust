import test from 'node:test';
import assert from 'node:assert/strict';
import {assertLocaleEvidence,preservePrimaryFailure} from './world_admin_live_locale.mjs';
const good={sameNode:true,draft:'owned unsaved draft',expectedDraft:'owned unsaved draft',callsBefore:3,callsAfter:3,readOnlyBefore:[true,true],readOnlyAfter:[true,true]};
test('equal retained-node/draft/read-only evidence without additional calls passes',()=>assert.doesNotThrow(()=>assertLocaleEvidence(good)));
for(const [name,delta]of Object.entries({remount:{sameNode:false},lostDraft:{draft:'reloaded'},extraOwnerRPC:{callsAfter:4},lostReadOnly:{readOnlyAfter:[false,true]}}))test(`${name} refuses`,()=>assert.throws(()=>assertLocaleEvidence({...good,...delta})));

test('local cleanup never masks a primary backend/assertion failure',async()=>{const primary=new Error('owned primary');await assert.rejects(async()=>{try{throw primary;}finally{await preservePrimaryFailure(primary,async()=>{throw new Error('owned cleanup');});}},error=>error===primary);});
test('cleanup failure without prior error still refuses qualification',async()=>{await assert.rejects(preservePrimaryFailure(null,async()=>{throw new Error('owned cleanup');}),/local cleanup failed/);});
