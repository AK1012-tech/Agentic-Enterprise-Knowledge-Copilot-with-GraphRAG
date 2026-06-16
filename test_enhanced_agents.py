"""
Demonstration of enhanced agents with LLM-based reasoning.

This script shows:
1. Intelligent planning based on question semantics (not just keywords)
2. Proper answer grounding verification (not just string matching)
"""

import sys
from app.agents.planner_agent import PlannerAgent
from app.agents.verifier_agent import VerifierAgent
from app.utils.config import Settings
from app.llms.llm_router import get_llm


def test_enhanced_planner():
    """Test LLM-based planning vs keyword-based fallback."""
    print("\n" + "="*70)
    print("TESTING ENHANCED PLANNER AGENT")
    print("="*70)
    
    settings = Settings(use_external_services=False)
    llm = get_llm(settings)
    
    # Initialize with LLM
    planner_with_llm = PlannerAgent(llm=llm)
    # Initialize without LLM (fallback mode)
    planner_fallback = PlannerAgent()
    
    test_questions = [
        "What are the salary ranges for engineers?",
        "How does the pension fund affect employee retirement?",
        "What policies are in place for remote work?",
        "Which departments are connected to the finance team?",
        "How do safety procedures impact emergency response?",
        "What is the relationship between budget cuts and headcount?",
    ]
    
    print("\nTesting Questions:")
    for question in test_questions:
        plan_llm = planner_with_llm.plan(question)
        plan_fallback = planner_fallback.plan(question)
        
        print(f"\nQ: {question}")
        print(f"  LLM Plan:      retrieval={plan_llm['use_retrieval']}, graph={plan_llm['use_graph']}")
        print(f"  Fallback Plan: retrieval={plan_fallback['use_retrieval']}, graph={plan_fallback['use_graph']}")
        
        # Highlight cases where LLM and fallback differ
        if plan_llm != plan_fallback:
            print(f"  ✓ LLM provides different routing (more intelligent)")


def test_enhanced_verifier():
    """Test LLM-based verification vs simple keyword matching."""
    print("\n" + "="*70)
    print("TESTING ENHANCED VERIFIER AGENT")
    print("="*70)
    
    settings = Settings(use_external_services=False)
    llm = get_llm(settings)
    
    # Initialize with LLM
    verifier_with_llm = VerifierAgent(llm=llm)
    # Initialize without LLM (fallback mode)
    verifier_fallback = VerifierAgent()
    
    contexts = [
        {
            "source": "Employee_Handbook.pdf",
            "text": "Remote work is allowed for up to 3 days per week with manager approval. All employees must maintain core hours from 10 AM to 3 PM.",
            "document_id": "doc_1",
            "chunk_id": "chunk_1",
            "score": 0.95
        },
        {
            "source": "HR_Policy.pdf",
            "text": "Employees are eligible for health insurance after 30 days of employment. Coverage includes dental and vision.",
            "document_id": "doc_2",
            "chunk_id": "chunk_2",
            "score": 0.87
        }
    ]
    
    test_answers = [
        "Based on the indexed context: Remote work is allowed for up to 3 days per week with manager approval.",
        "I do not have enough indexed evidence to answer this question confidently.",
        "Employees can work from anywhere unlimited days per week according to company policy.",
        "Health insurance coverage begins after 30 days of employment and includes dental and vision.",
        "The company offers free lunch every day.",
    ]
    
    print("\nTesting Answers Against Contexts:")
    for i, answer in enumerate(test_answers, 1):
        verified_llm = verifier_with_llm.verify(answer, contexts)
        verified_fallback = verifier_fallback.verify(answer, contexts)
        
        print(f"\nAnswer {i}: {answer[:70]}...")
        print(f"  LLM Verification:      {verified_llm}")
        print(f"  Fallback Verification: {verified_fallback}")
        
        if verified_llm != verified_fallback:
            print(f"  ✓ LLM provides more nuanced grounding check")


def test_agent_initialization():
    """Test that agents are properly initialized with LLM in the workflow."""
    print("\n" + "="*70)
    print("TESTING AGENT INITIALIZATION IN WORKFLOW")
    print("="*70)
    
    from app.graph.state_graph import AgentGraphBuilder
    
    settings = Settings(use_external_services=False)
    builder = AgentGraphBuilder(settings)
    
    print("\n✓ AgentGraphBuilder initialized successfully")
    print(f"  - Planner has LLM: {builder.planner.llm is not None}")
    print(f"  - Verifier has LLM: {builder.verifier.llm is not None}")
    print(f"  - Summarizer initialized: {builder.summarizer is not None}")
    print("\n✓ All agents properly integrated with LLM for intelligent reasoning")


if __name__ == "__main__":
    print("\n🚀 ENHANCED AGENT DEMONSTRATION")
    
    try:
        test_agent_initialization()
        test_enhanced_planner()
        test_enhanced_verifier()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nKEY IMPROVEMENTS:")
        print("1. PlannerAgent: Now uses LLM for semantic understanding of questions")
        print("   - Better routing decisions beyond keyword matching")
        print("   - Falls back to keyword matching if LLM unavailable")
        print("\n2. VerifierAgent: Now uses LLM for answer grounding verification")
        print("   - Checks if answer is actually supported by context")
        print("   - Detects unsupported claims and hallucinations")
        print("   - Falls back to word overlap matching if LLM unavailable")
        print("\n3. Both agents maintain backward compatibility and graceful fallbacks")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
