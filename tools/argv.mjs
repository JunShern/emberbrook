/* argv.mjs — THE FLAG PARSER, SHARED, AND IT ACCEPTS `--key=value`.
 *
 * WHY IT EXISTS (2026-08-05, round 24, found in the first command of the round).
 * Every instrument in this repo carried its own copy of one line:
 *
 *     const arg = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i+1] : d; };
 *
 * That line matches `--from ch2.supper` and DOES NOT MATCH `--from=ch2.supper`. It does
 * not error on the second form: `indexOf` returns -1 and the tool quietly uses its own
 * DEFAULT. So `wayfind_probe --from=ch2.supper` measured `ch2.winches`, printed a full
 * page of correct-looking numbers, and the only reason anybody noticed is that the tool
 * happens to echo its seed. Round 23's `--from=ch2.maren` reading was the same shape and
 * is re-measured in round 24 because of it.
 *
 * THE DEFECT IS NOT THE MISSING `=`; IT IS THAT A MISSPELLED FLAG IS INDISTINGUISHABLE
 * FROM AN ABSENT ONE. So this module does two things:
 *   - `arg(k, d)` accepts BOTH `--k v` and `--k=v`;
 *   - `checkArgs(label)` REFUSES TO RUN on any `--token` the tool never asked for. An
 *     instrument that silently ignores its own steering measures a different world than
 *     the one you asked about, which is the same class as cdp.mjs's rule: an instrument
 *     that finds nothing must prove it could have found something.
 *
 * `knownKeys` pre-seeds the asked set for tools whose `arg()` calls sit inside branches
 * (`_court_probe` asks for `--comp` only in the --comp path), because checkArgs runs
 * before those branches do.
 */
export function mkArg(source, knownKeys = []) {
  const argv = Array.isArray(source) ? source : process.argv;
  const asked = new Set(knownKeys);
  const arg = (k, d) => {
    asked.add(k);
    const eq = argv.find(t => typeof t === 'string' && t.startsWith('--' + k + '='));
    if (eq !== undefined) return eq.slice(k.length + 3);
    const i = argv.indexOf('--' + k);
    return i >= 0 ? argv[i + 1] : d;
  };
  const checkArgs = (label = 'tool') => {
    const bad = [];
    for (const t of argv) {
      if (typeof t !== 'string' || !t.startsWith('--')) continue;
      const k = t.slice(2).split('=')[0];
      if (!asked.has(k)) bad.push(t);
    }
    if (bad.length) {
      console.error(`${label}: UNKNOWN FLAG${bad.length > 1 ? 'S' : ''} ${bad.join(' ')}`);
      console.error(`${label}: refusing to run — a flag this tool does not read is a ` +
        `measurement of a different question than the one you asked.`);
      console.error(`${label}: flags it does read: ${[...asked].sort().map(k => '--' + k).join(' ')}`);
      process.exit(2);
    }
    return true;
  };
  return { arg, checkArgs };
}
