import unittest
from unittest.mock import patch
from types import SimpleNamespace
from eval.metrics import score
from eval.costs import price_call, economics
from eval.run_eval import validate
from telemetry import capture,measured,stage
from feedback import generate_report,validate_report
from interviewer import generate_followup

REPORT=dict(overall_score=7,overall_summary='Some gaps.',strengths=[],weaknesses=[],next_steps=[])
TRANSCRIPT=[dict(question='How would you measure invoice success?',answer='I would measure on time payment rates for small businesses.')]
class EvaluationTests(unittest.TestCase):
    def test_failure_on_clean_case_is_not_exact_pass(self):
        s=score([dict(expected_tags=[],predicted_tags=[],completed=False)])
        self.assertEqual(s['exact_set_accuracy'],0)
        self.assertIsNone(s['recall'])
    def test_micro_metrics(self):
        s=score([dict(expected_tags=['a','b'],predicted_tags=['a','c'],completed=True)])
        self.assertEqual((s['recall'],s['precision'],s['f1']),(.5,.5,.5))
    def test_alignment_guard(self):
        c=dict(id='a',question='Q',answer='A',expected_tags=[],expected_behavior='ok',transcript=[dict(question='wrong',answer='A')])
        with self.assertRaises(ValueError):validate(dict(cases=[c]))
    def test_final_review_required(self):
        with self.assertRaises(ValueError):validate(dict(cases=[]),True)
    def test_usage_kept_on_parse_failure_boundary(self):
        records=[]
        response=SimpleNamespace(usage_metadata=SimpleNamespace(model_dump=lambda **kw:dict(prompt_token_count=2)),model_version='m')
        with capture(records),stage('final_feedback'):
            self.assertIs(measured(lambda c,m:response,None,'m'),response)
        self.assertEqual(records[0]['usage']['prompt_token_count'],2)
    def test_unknown_cost_not_zero(self):
        self.assertIsNone(price_call(dict(model='m',usage=None,status='error'),{}))
    def test_price_thoughts_and_cache(self):
        call=dict(model='m',status='ok',stage='final_feedback',usage=dict(prompt_token_count=100,candidates_token_count=20,thoughts_token_count=5,cached_content_token_count=10))
        prices=dict(models={'m':dict(source='official',verified_on='date',input_per_million=1,output_per_million=2,cached_input_per_million=.5,output_includes_thoughts=True)})
        self.assertAlmostEqual(price_call(call,prices),145/1e6)
    def test_short_answer_no_api(self):
        with patch('feedback.generate_json') as api:
            r=generate_report([dict(question='Q',answer='')])
            api.assert_not_called()
        self.assertEqual(r['report']['overall_score'],1)
    def test_off_topic_receives_low_score(self):
        with patch('feedback.generate_json',return_value=dict(items=[dict(index=0,status='off_topic',reason='Wrong task')])):
            r=generate_report(TRANSCRIPT)
        self.assertEqual(r['report']['overall_score'],1)
        self.assertEqual(r['report']['weaknesses'][0]['tag'],'off_topic')
    def test_schema_rejects_out_of_range(self):
        self.assertFalse(validate_report(dict(REPORT,overall_score=999))[0])
    def test_followup_rejects_string_false(self):
        with patch('interviewer.generate_json',return_value=dict(in_scope='false',follow_up='Why?')):
            self.assertTrue(generate_followup('Q','A')['fallback_used'])
    def test_modes_share_final_prompt_and_one_rubric(self):
        rubric=dict(tag='no_success_metric',title='Metrics',text='Use a measurable outcome.')
        relevance=dict(items=[dict(index=0,status='relevant',reason='On task')])
        final_inputs=[]
        def fake_json(system,user,**kwargs):
            if kwargs.get('schema').__name__=='RelevanceResult':return relevance
            final_inputs.append((system,user));return dict(REPORT)
        def tool_factory(log,results):
            def lookup(tag):
                log.append(dict(name='lookup_rubric_by_tag',argument=dict(tag=tag),result_id=tag));results.append(rubric)
            return lookup
        with patch('feedback.generate_json',side_effect=fake_json),patch('feedback.create_lookup_rubric_tool',side_effect=tool_factory),patch('feedback.generate_with_tools',return_value=[SimpleNamespace(name='lookup_rubric_by_tag',args=dict(tag='no_success_metric'))]),patch('retrieval.retrieve',return_value=[rubric]) as retrieval:
            for mode in ('tool','embedding'):
                r=generate_report(TRANSCRIPT,retrieval_mode=mode)
                self.assertEqual(len(r['meta']['retrieved_tags']),1)
            self.assertEqual(final_inputs[0],final_inputs[1])
            self.assertEqual(retrieval.call_args.kwargs['k'],1)
    def test_bad_tool_argument_rejected(self):
        from llm import LLMError
        with patch('feedback.generate_json',return_value=dict(items=[dict(index=0,status='relevant',reason='ok')])),patch('feedback.generate_with_tools',return_value=[SimpleNamespace(name='lookup_rubric_by_tag',args=dict(tag='invented'))]):
            with self.assertRaises(LLMError):generate_report(TRANSCRIPT)
    def test_sensitivity_flip(self):
        a=dict(users=200,sessions_per_user_year=6,hosting_monthly=25,storage_monthly=0,other_monthly=0,maintenance_hours_monthly=2,maintenance_hourly_rate=30,build_hours=40,build_hourly_rate=30,minutes_saved=10,time_value_hourly=20,index_builds_year=0,index_build_cost=0)
        e=economics(.01,a)
        self.assertLess(e[0]['net_first_year'],0);self.assertGreater(e[1]['net_first_year'],0)


class WorkflowTests(unittest.TestCase):
    def test_run_and_report_without_network(self):
        import json, tempfile, sys
        from pathlib import Path
        from eval import run_eval, report
        data=dict(unit='single_answer_report',reviewed_by='reviewer',cases=[dict(id='case',question='Q',answer='A full answer with enough words.',expected_tags=[],category='ordinary',expected_behavior='Answer relevantly',provenance='test fixture',reviewed_by='reviewer')])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dataset=root/'cases.json';dataset.write_text(json.dumps(data))
            with patch.object(sys,'argv',['run_eval','--dataset',str(dataset),'--freeze']):run_eval.main()
            fake=dict(report=REPORT,meta=dict(rule_based=False,formatting_failures=0,retrieved_tags=[]))
            with patch.object(sys,'argv',['run_eval','--dataset',str(dataset),'--out',str(root/'runs'),'--modes','none','--repeats','1','--sleep','0','--final','--run']),patch('feedback.generate_report',return_value=fake):
                run_eval.main()
            run=next((root/'runs').iterdir())
            with patch.object(sys,'argv',['report',str(run)]):report.main()
            self.assertTrue((run/'session09_report.md').exists())
            self.assertIn('PENDING',(run/'session09_report.md').read_text())
            self.assertEqual(len((run/'results.jsonl').read_text().splitlines()),1)
    def test_streamlit_initial_page(self):
        from streamlit.testing.v1 import AppTest
        from pathlib import Path
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'), default_timeout=15).run()
        self.assertEqual(len(app.exception),0)

class SubmissionTests(unittest.TestCase):
    def test_preserve_original_and_continuation(self):
        from transcript_state import record_submission
        transcript=[]
        record_submission(transcript,'Q',0,'Oops')
        record_submission(transcript,'Q',0,'Here is my completed answer.')
        self.assertEqual(len(transcript),1)
        self.assertEqual(transcript[0]['answer_submissions'],['Oops','Here is my completed answer.'])
        self.assertIn('Oops',transcript[0]['answer'])
        record_submission(transcript,'Q',0,'A short followup',True)
        self.assertEqual(transcript[0]['follow_up_answer'],'A short followup')
    def test_mixed_interview_retains_off_topic_text_and_caps_score(self):
        transcript=TRANSCRIPT+[dict(question='How do you prioritize?',answer='I really enjoy cycling in the mountains on weekends.')]
        relevance=dict(items=[dict(index=0,status='relevant',reason='ok'),dict(index=1,status='off_topic',reason='cycling')])
        with patch('feedback.generate_json',side_effect=[relevance,dict(REPORT,overall_score=10)]) as call:
            result=generate_report(transcript,retrieval_mode='none')
        self.assertIn('cycling in the mountains',call.call_args.args[1])
        self.assertEqual(result['report']['overall_score'],6)
        self.assertEqual(result['report']['weaknesses'][0]['tag'],'off_topic')
    def app(self):
        from streamlit.testing.v1 import AppTest
        from pathlib import Path
        return AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'), default_timeout=15).run()
    def test_start_over_resets_counter(self):
        app=self.app()
        app.sidebar.button[0].click().run()
        app.session_state['requests']=9
        app.sidebar.button[0].click().run()
        self.assertEqual(app.session_state['requests'],0)
        self.assertEqual(app.session_state['transcript'],[])
    def test_short_submission_visible_and_recoverable(self):
        app=self.app();app.sidebar.button[0].click().run()
        app.chat_input[0].set_value('Oops').run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.session_state['transcript'][0]['answer'],'Oops')
        self.assertTrue(any(w.value == 'That is too short to assess. Please write a fuller answer.' for w in app.warning))
        self.assertFalse(any('Your response is saved above' in text for _,text in app.session_state['messages']))
        self.assertEqual(app.session_state['q_idx'],0)
        self.assertIn(('user','Oops'),app.session_state['messages'])
        self.assertEqual(app.session_state['phase'],'answer')
    def test_off_topic_submission_saved(self):
        app=self.app();app.sidebar.button[0].click().run()
        with patch('interviewer.generate_followup',return_value=dict(in_scope=False,follow_up='',fallback_used=False)):
            app.chat_input[0].set_value('I enjoy cycling around the city.').run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.session_state['transcript'][0]['answer'],'I enjoy cycling around the city.')
        self.assertEqual(app.session_state['phase'],'answer')
    def test_api_failure_does_not_lose_answer(self):
        from llm import LLMError
        app=self.app();app.sidebar.button[0].click().run()
        with patch('interviewer.generate_followup',side_effect=LLMError('unavailable')):
            app.chat_input[0].set_value('I would first define the success metric.').run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.session_state['transcript'][0]['answer'],'I would first define the success metric.')

class TaxonomyTests(unittest.TestCase):
    def test_schema_app_and_evaluator_agree_on_ten_weaknesses(self):
        from typing import get_args
        from schemas import Tag, Weakness
        from feedback import TAXONOMY
        from eval.run_eval import TAGS
        self.assertEqual(set(get_args(Tag)),set(TAXONOMY))
        self.assertEqual(set(TAXONOMY),TAGS)
        self.assertEqual(len(TAGS),10)
        for tag in ('no_business_impact','vague_solution','unstructured'):
            self.assertEqual(Weakness(tag=tag,evidence='Evidence',fix='Fix').tag,tag)
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            Weakness(tag='product_strategy',evidence='Evidence',fix='Fix')
    def test_tool_documents_and_resolves_new_rubrics(self):
        from tools import create_lookup_rubric_tool
        log=[];results=[];tool=create_lookup_rubric_tool(log,results)
        for tag in ('no_business_impact','vague_solution','unstructured'):
            self.assertIn(tag,tool.__doc__)
            self.assertEqual(tool(tag)['tag'],tag)
        self.assertEqual(len(log),3)
    def test_new_drafts_are_valid_and_unreviewed(self):
        import json
        from pathlib import Path
        from eval.run_eval import validate
        data=json.loads((Path(__file__).resolve().parents[1]/'eval/datasets/development.json').read_text())
        self.assertTrue(validate(data))
        for tag in ('no_business_impact','vague_solution','unstructured'):
            case=next(c for c in data['cases'] if c['id']=='draft_'+tag)
            self.assertEqual(case['expected_tags'],[tag])
            self.assertEqual(case['reviewed_by'],'')
            self.assertIn('AI-drafted',case['provenance'])

class PromptVersionTests(unittest.TestCase):
    def test_v4_preserves_v3_and_other_prompt_controls(self):
        from prompts import FEEDBACK_PROMPTS,FOLLOWUP_PROMPTS,ACTIVE_VERSION
        self.assertTrue(FEEDBACK_PROMPTS['v4'].startswith(FEEDBACK_PROMPTS['v3']))
        self.assertIn('1. Identify',FEEDBACK_PROMPTS['v4'])
        self.assertEqual(FOLLOWUP_PROMPTS['v3'],FOLLOWUP_PROMPTS['v4'])
        self.assertEqual(ACTIVE_VERSION,'v3')
    def test_only_final_system_instruction_changes(self):
        from prompts import FEEDBACK_PROMPTS
        relevance=dict(items=[dict(index=0,status='relevant',reason='ok')])
        requests=[]
        for version in ('v3','v4'):
            with patch('feedback.generate_json',side_effect=[relevance,dict(REPORT)]) as api:
                generate_report(TRANSCRIPT,retrieval_mode='none',version=version)
                requests.append(api.call_args_list)
        self.assertEqual(requests[0][0],requests[1][0])
        self.assertEqual(requests[0][1].args[1],requests[1][1].args[1])
        self.assertEqual(requests[0][1].kwargs,requests[1][1].kwargs)
        self.assertEqual(requests[1][1].args[0],FEEDBACK_PROMPTS['v4'])
    def test_two_versions_stay_separate_in_saved_results_and_report(self):
        import json,tempfile,sys,csv
        from pathlib import Path
        from eval import run_eval,report
        data=dict(unit='single_answer_report',cases=[dict(id='case',question='Q',answer='A substantial answer for this question.',expected_tags=[],category='ordinary',expected_behavior='Relevant')])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dataset=root/'cases.json';dataset.write_text(json.dumps(data))
            fake=dict(report=REPORT,meta=dict(rule_based=False,formatting_failures=0,retrieved_tags=[]))
            with patch.object(sys,'argv',['run_eval','--dataset',str(dataset),'--out',str(root/'runs'),'--versions','v3','v4','--modes','none','--repeats','1','--sleep','0','--run']),patch('feedback.generate_report',return_value=fake):
                run_eval.main()
            folder=next((root/'runs').iterdir())
            with patch.object(sys,'argv',['report',str(folder)]):report.main()
            manifest=json.loads((folder/'manifest.json').read_text())
            self.assertEqual(manifest['versions'],['v3','v4'])
            self.assertEqual(set(manifest['feedback_prompts']),{'v3','v4'})
            with (folder/'comparison.csv').open() as f: rows=list(csv.DictReader(f))
            self.assertEqual({r['version'] for r in rows},{'v3','v4'})
            with (folder/'human_review.csv').open() as f: reviews=list(csv.DictReader(f))
            self.assertEqual(len(reviews),2)
            text=(folder/'session09_report.md').read_text()
            self.assertIn('v3 / none',text);self.assertIn('v4 / none',text)

if __name__=='__main__':unittest.main()
