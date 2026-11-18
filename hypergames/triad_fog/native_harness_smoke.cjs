/* TS-HG-02: Load public scenario with the actual compiled native harness. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const base = path.resolve(__dirname, '../..');
const { loadSessionConfigFromPath } = require(path.join(base, 'dist-harness/harness/config.js'));
const { HeadlessPlaytestSession } = require(path.join(base, 'dist-harness/harness/HeadlessPlaytestSession.js'));

async function main(){
  const configPath=path.join(base, 'playtest/sample-triad-fog-tournament.json');
  const scenarioPath=path.join(base, 'playtest/scenarios/three-voices-fog.json');
  const scenario=JSON.parse(fs.readFileSync(scenarioPath,'utf8'));
  const config=await loadSessionConfigFromPath(configPath);
  assert.deepEqual(Object.keys(config.agents).sort(),
    ['HEGEMON','STATE','INFILTRATOR','BROKER','ARCHIVIST'].sort());
  assert.deepEqual(config.scenario,scenario);
  const session=new HeadlessPlaytestSession(config,'ts-hg-02-public-only-smoke');
  const snap=session.getSnapshot();
  assert.equal(snap.scenario.name,scenario.name);
  for(const faction of scenario.factions){
    assert.equal(snap.state.factions[faction.id].flops,faction.flops);
    assert.equal(snap.state.factions[faction.id].influence,faction.influence);
  }
  assert.equal(snap.state.counters.tas,scenario.counters.tas);
  assert.equal(snap.state.counters.pressures.memetic,scenario.counters.pressures.memetic);
  const serialized=JSON.stringify(config.scenario);
  for(const forbidden of ['"btc_disputed"','"rsi_depth"','"sae_fidelity"',
                           '"eval_robustness"','"evaluation_shift"',
                           '"btc_escrow_pool"','"p2Values"']){
    assert(!serialized.includes(forbidden),`hidden data escaped: ${forbidden}`);
  }
  console.log(JSON.stringify({schema:'TS-HG-02/native-smoke-v1',
    focal_factions:scenario.factions.map(f=>f.id),
    native_active_seats:Object.keys(config.agents),
    state_has_public_scenario:true,private_data_absent:true,passed:true}));
}
main().catch(err=>{console.error(err);process.exitCode=1;});
