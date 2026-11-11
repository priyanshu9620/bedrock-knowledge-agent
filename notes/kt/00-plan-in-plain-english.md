# The plan in plain English

**What we build.** A question-answering assistant for a (fictional) company handbook. The documents sit in S3. A Bedrock
Knowledge Base turns them into searchable vectors. A Bedrock Agent takes a question, pulls the relevant passages, and when
the question needs live numbers (your leave balance, a reimbursement amount, a holiday list) it calls a Lambda function
through an "action group" — a small API we describe with an OpenAPI schema. Answers cite the passages they used.

**Why the handbook.** We write it, so we know every answer; answer quality can be scored by rules, not by opinion.

**How we keep it cheap.** Vectors live in S3 Vectors (pay per use, nothing idle). The whole stack is created, filled,
evaluated and destroyed in one sitting. Target: under two dollars for the entire project.

**How we get numbers.** ~40 fixed questions in four classes; a script asks each, checks the fact, the citation, the tool
call and the refusal, and writes the report. Nothing is typed in by hand.
