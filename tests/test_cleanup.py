"""Exercise the actual Bash cleanup function without recording or clipboard access."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'voice-memo'


def cleanup_shell():
    text = SOURCE.read_text()
    return text[text.index('AI_PROMPT='):text.index('# ESC path:')]


class CleanupTests(unittest.TestCase):
    def run_cleanup(self, stub, **overrides):
        with tempfile.TemporaryDirectory() as directory:
            pi = Path(directory) / 'pi'
            pi.write_text('#!/bin/bash\n' + stub)
            pi.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if not k.startswith('VOICE_MEMO_AI')}
            env.update(PATH=directory + ':' + env['PATH'], VOICE_MEMO_AI_ENGINE='pi')
            env.update(overrides)
            return subprocess.run(['bash', '-c', cleanup_shell() + '\nai_cleanup "um hello world"'],
                                  env=env, text=True, capture_output=True, timeout=10)

    def test_failure_discards_partial_output(self):
        result = self.run_cleanup("printf 'Partial output'; exit 1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_timeout_discards_partial_output(self):
        result = self.run_cleanup("printf 'Partial output'; sleep 3", VOICE_MEMO_AI_TIMEOUT='0.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_empty_response_returns_empty_for_caller_fallback(self):
        result = self.run_cleanup('exit 0')
        self.assertEqual(result.stdout, '')

    def test_provider_and_model_overrides(self):
        result = self.run_cleanup('''[[ " $* " == *" --provider google "* ]] || exit 2
[[ " $* " == *" --model custom-model "* ]] || exit 3
printf 'Override works'
''', VOICE_MEMO_AI_PROVIDER='google', VOICE_MEMO_AI_MODEL='custom-model')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'Override works')

    def test_pi_flags_and_stdin(self):
        stub = '''args=" $* "
for flag in --print --no-session --no-tools --no-extensions --no-skills --no-context-files --no-prompt-templates; do
  [[ "$args" == *" $flag "* ]] || exit 2
done
[[ "$args" == *" --provider openrouter "* ]] || exit 3
[[ "$args" == *" --model google/gemini-3.7-flash "* ]] || exit 4
[[ "$args" == *" --thinking off "* ]] || exit 5
[[ "$args" == *" --system-prompt "* ]] || exit 6
input=$(</dev/stdin)
[[ "$input" == 'um hello world' ]] || exit 7
printf 'Hello world.'
'''
        result = self.run_cleanup(stub)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'Hello world.')


if __name__ == '__main__':
    unittest.main()
