"""
Evaluation Endpoint for AI Explanations
POST /ai/evaluate-explanation/<explanation_id>/
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse

from core_ai.services.evaluation_service import ExplanationEvaluator
from core_ai.mongo_utils import get_mongo_db
from bson import ObjectId


@api_view(['POST'])
@permission_classes([AllowAny])
def evaluate_explanation(request, explanation_id):
    """
    Evaluate an AI explanation using 4-layer scoring system
    
    Args:
        request: HTTP request
        explanation_id: ID of the explanation to evaluate
        
    Returns:
        JSON response with evaluation results
    """
    
    try:
        # Validate explanation exists in MongoDB
        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Database connection failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        explanation_collection = db["ai_explanations"]
        explanation = explanation_collection.find_one({"_id": ObjectId(explanation_id)})
        
        if explanation is None:
            return Response(
                {"error": f"Explanation with ID {explanation_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Run evaluation
        evaluator = ExplanationEvaluator()
        evaluation_result = evaluator.evaluate_explanation(explanation_id)
        
        # Return simplified response
        response_data = {
            "evaluation_id": evaluation_result.get("evaluated_at"),
            "final_score": evaluation_result["final_score"],
            "verdict": evaluation_result["overall_verdict"],
            "weight_mode": evaluation_result["weight_mode"],
            "layer_scores": {
                "ast_cross_check": evaluation_result["layer1"]["score"],
                "completeness": evaluation_result["layer2"]["score"],
                "llm_judge": evaluation_result["layer3"]["score"],
                "human_review": evaluation_result["layer4"]["human_score"]
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Evaluation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_evaluation_history(request, explanation_id):
    """
    Get evaluation history for an explanation
    
    Args:
        request: HTTP request
        explanation_id: ID of the explanation
        
    Returns:
        JSON response with evaluation history
    """
    
    try:
        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Database connection failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        collection = db["explanation_evaluations"]
        
        # Find all evaluations for this explanation
        evaluations = list(collection.find(
            {"explanation_id": explanation_id},
            {"_id": 0}
        ).sort("evaluated_at", -1))
        
        return Response({
            "explanation_id": explanation_id,
            "evaluations": evaluations,
            "total_evaluations": len(evaluations)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to get evaluation history: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_evaluation_stats(request):
    """
    Get overall evaluation statistics
    
    Returns:
        JSON response with evaluation statistics
    """
    
    try:
        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Database connection failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        collection = db["explanation_evaluations"]
        
        # Calculate statistics
        total_evaluations = collection.count_documents({})
        
        # Get verdict distribution
        pipeline = [
            {"$group": {"_id": "$overall_verdict", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        verdict_distribution = list(collection.aggregate(pipeline))
        
        # Get average scores
        avg_score_pipeline = [
            {"$group": {"_id": None, "avg_score": {"$avg": "$final_score"}}}
        ]
        avg_score_result = list(collection.aggregate(avg_score_pipeline))
        avg_score = avg_score_result[0]["avg_score"] if avg_score_result else 0.0
        
        return Response({
            "total_evaluations": total_evaluations,
            "average_score": avg_score,
            "verdict_distribution": verdict_distribution
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to get evaluation stats: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_human_review(request, explanation_id):
    """
    Submit a human review score for an explanation.
    Body: {"score": 0.85, "comment": "optional comment"}
    Score must be between 0.0 and 1.0
    """
    try:
        score = request.data.get("score")
        comment = request.data.get("comment", "")

        if score is None:
            return Response({"error": "score is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            score = float(score)
        except (ValueError, TypeError):
            return Response({"error": "score must be a number"}, status=status.HTTP_400_BAD_REQUEST)

        if not (0.0 <= score <= 1.0):
            return Response({"error": "score must be between 0.0 and 1.0"}, status=status.HTTP_400_BAD_REQUEST)

        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save human feedback
        from datetime import datetime
        db["human_feedback"].update_one(
            {"explanation_id": explanation_id},
            {"$set": {
                "explanation_id": explanation_id,
                "score": score,
                "comment": comment,
                "reviewed_at": datetime.utcnow()
            }},
            upsert=True
        )

        # Re-evaluate with human score included (force_reevaluate=True)
        evaluator = ExplanationEvaluator()
        evaluation_result = evaluator.evaluate_explanation(explanation_id, force_reevaluate=True)

        return Response({
            "message": "Human review submitted and evaluation updated.",
            "final_score": evaluation_result["final_score"],
            "final_score_percentage": evaluation_result["final_score_percentage"],
            "verdict": evaluation_result["overall_verdict"],
            "human_reviewed": True,
            "layer_scores": {
                "ast_cross_check": evaluation_result["layer1"]["score"],
                "completeness": evaluation_result["layer2"]["score"],
                "llm_judge": evaluation_result["layer3"]["score"],
                "human_review": score
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": f"Failed to submit review: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
